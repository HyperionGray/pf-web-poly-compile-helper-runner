/**
 * Simple In-Memory Cache Implementation
 * 
 * Provides a lightweight caching layer for frequently accessed data
 * with TTL (Time To Live) support and automatic cleanup.
 */

export class SimpleCache {
  constructor(options = {}) {
    this.maxSize = options.maxSize || 100; // Maximum number of entries
    this.defaultTTL = options.defaultTTL || 300000; // Default TTL: 5 minutes
    this.cleanupInterval = options.cleanupInterval || 60000; // Cleanup every minute
    this.cache = new Map();
    this.pendingFactories = new Map(); // Track in-flight factory calls
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      evictions: 0
    };
    
    // Start automatic cleanup
    this.startCleanup();
  }

  /**
   * Get a value from cache
   * @param {string} key - Cache key
   * @returns {*} Cached value or undefined
   */
  get(key) {
    const entry = this.cache.get(key);
    
    if (!entry) {
      this.stats.misses++;
      return undefined;
    }
    
    // Check if entry has expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      this.stats.misses++;
      return undefined;
    }
    
    // Update access time for LRU tracking
    entry.lastAccessed = Date.now();
    this.stats.hits++;
    return entry.value;
  }

  /**
   * Set a value in cache
   * @param {string} key - Cache key
   * @param {*} value - Value to cache
   * @param {number} ttl - Time to live in milliseconds (optional)
   */
  set(key, value, ttl = this.defaultTTL) {
    // If cache is full, evict least recently used entry
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      this.evictLRU();
    }
    
    const now = Date.now();
    this.cache.set(key, {
      value,
      createdAt: now,
      lastAccessed: now,
      expiresAt: now + ttl
    });
    
    this.stats.sets++;
  }

  /**
   * Check if a key exists in cache and is not expired
   * @param {string} key - Cache key
   * @returns {boolean}
   */
  has(key) {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return false;
    }
    
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }

  /**
   * Delete a key from cache
   * @param {string} key - Cache key
   * @returns {boolean} True if key was deleted
   */
  delete(key) {
    const result = this.cache.delete(key);
    if (result) {
      this.stats.deletes++;
    }
    return result;
  }

  /**
   * Clear all entries from cache
   */
  clear() {
    const size = this.cache.size;
    this.cache.clear();
    this.stats.deletes += size;
  }

  /**
   * Get or set a value (cache-aside pattern)
   * Prevents duplicate factory calls for the same key by tracking in-flight operations
   * @param {string} key - Cache key
   * @param {Function} factory - Async function to generate value if not cached
   * @param {number} ttl - Time to live in milliseconds (optional)
   * @returns {Promise<*>} Cached or generated value
   */
  async getOrSet(key, factory, ttl = this.defaultTTL) {
    // Try to get from cache first
    const cached = this.get(key);
    if (cached !== undefined) {
      return cached;
    }
    
    // Check if factory is already running for this key
    if (this.pendingFactories.has(key)) {
      return this.pendingFactories.get(key);
    }
    
    // Generate value and cache it
    const factoryPromise = factory().then(value => {
      this.set(key, value, ttl);
      this.pendingFactories.delete(key);
      return value;
    }).catch(error => {
      this.pendingFactories.delete(key);
      throw error;
    });
    
    this.pendingFactories.set(key, factoryPromise);
    return factoryPromise;
  }

  /**
   * Evict least recently used entry
   */
  evictLRU() {
    let oldestKey = null;
    let oldestTime = Infinity;
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed;
        oldestKey = key;
      }
    }
    
    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.stats.evictions++;
    }
  }

  /**
   * Clean up expired entries
   */
  cleanup() {
    const now = Date.now();
    const keysToDelete = [];
    
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        keysToDelete.push(key);
      }
    }
    
    for (const key of keysToDelete) {
      this.cache.delete(key);
    }
    
    return keysToDelete.length;
  }

  /**
   * Start automatic cleanup timer
   */
  startCleanup() {
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.cleanupInterval);
    
    // Don't prevent process from exiting
    if (this.cleanupTimer.unref) {
      this.cleanupTimer.unref();
    }
  }

  /**
   * Stop automatic cleanup timer and clean up resources
   * Call this when the cache instance is no longer needed to prevent memory leaks
   */
  stopCleanup() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }
  
  /**
   * Destroy the cache instance and release all resources
   * Stops cleanup timer and clears all cached data
   */
  destroy() {
    this.stopCleanup();
    this.cache.clear();
    this.pendingFactories.clear();
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  getStats() {
    const hitRate = this.stats.hits + this.stats.misses > 0
      ? (this.stats.hits / (this.stats.hits + this.stats.misses)) * 100
      : 0;
    
    return {
      ...this.stats,
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate: hitRate.toFixed(2) + '%'
    };
  }

  /**
   * Reset cache statistics
   */
  resetStats() {
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      evictions: 0
    };
  }

  /**
   * Get all cache keys
   * @returns {Array<string>} Array of cache keys
   */
  keys() {
    return Array.from(this.cache.keys());
  }

  /**
   * Get cache size
   * @returns {number} Number of entries in cache
   */
  size() {
    return this.cache.size;
  }
}

/**
 * Create a cache with specific configuration
 * @param {Object} options - Configuration options
 * @returns {SimpleCache} Configured cache instance
 */
export function createCache(options = {}) {
  return new SimpleCache(options);
}

/**
 * Singleton cache instance for application-wide use
 */
export const appCache = createCache({
  maxSize: 500,
  defaultTTL: 300000, // 5 minutes
  cleanupInterval: 60000 // 1 minute
});

/**
 * Example usage:
 * 
 * import { SimpleCache, appCache } from './simple-cache.mjs';
 * 
 * // Create a custom cache
 * const myCache = new SimpleCache({
 *   maxSize: 100,
 *   defaultTTL: 300000
 * });
 * 
 * // Set and get values
 * myCache.set('user:123', { name: 'John', age: 30 });
 * const user = myCache.get('user:123');
 * 
 * // Use cache-aside pattern
 * const data = await myCache.getOrSet('expensive:data', async () => {
 *   // This function only runs if data is not in cache
 *   return await fetchExpensiveData();
 * }, 600000); // Cache for 10 minutes
 * 
 * // Use singleton cache
 * appCache.set('config', { theme: 'dark' });
 * const config = appCache.get('config');
 * 
 * // Check cache stats
 * console.log(appCache.getStats());
 */

export default SimpleCache;

// C++ example - more complex debugging scenarios
#include <iostream>
#include <vector>
#include <string>
#include <memory>

class Player {
private:
    std::string name;
    int score;
    
public:
    Player(const std::string& n, int s) : name(n), score(s) {}
    
    void display() const {
        std::cout << "Player: " << name << ", Score: " << score << std::endl;
    }
    
    int getScore() const { return score; }
    void addScore(int points) { score += points; }
};

void process_players(std::vector<Player>& players) {
    std::cout << "\n=== Processing Players ===\n";
    
    for (auto& player : players) {
        player.display();
    }
    
    // Calculate total score
    int total = 0;
    for (const auto& player : players) {
        total += player.getScore();
    }
    
    std::cout << "Total score: " << total << std::endl;
}

void recursive_countdown(int n) {
    std::cout << "Countdown: " << n << std::endl;
    
    if (n <= 0) {
        std::cout << "Blast off! 🚀\n";
        return;
    }
    
    recursive_countdown(n - 1);
}

int main(int argc, char* argv[]) {
    std::cout << "=== Debug Practice Program (C++) ===\n\n";
    
    // Create some players
    std::vector<Player> players;
    players.emplace_back("Alice", 100);
    players.emplace_back("Bob", 150);
    players.emplace_back("Charlie", 200);
    
    process_players(players);
    
    std::cout << "\n=== Recursive Function Test ===\n";
    recursive_countdown(5);
    
    // Smart pointer example
    std::cout << "\n=== Smart Pointer Example ===\n";
    auto ptr = std::make_unique<Player>("Dave", 300);
    ptr->display();
    
    std::cout << "\nProgram completed successfully!\n";
    return 0;
}

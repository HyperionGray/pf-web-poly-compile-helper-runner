; ModuleID = 'lib_simple.6f51c73daefd9f23-cgu.0'
source_filename = "lib_simple.6f51c73daefd9f23-cgu.0"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@alloc_16e8aa63d85f9e3bf36e816361a3f3a5 = private unnamed_addr constant [79 x i8] c"/rustc/ed61e7d7e242494fb7057f2657300d9e77bb4fcb/library/core/src/iter/range.rs\00", align 1
@alloc_f6c93850c917906f08a9412dbf717571 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_16e8aa63d85f9e3bf36e816361a3f3a5, [16 x i8] c"N\00\00\00\00\00\00\00\AB\01\00\00\01\00\00\00" }>, align 8
@alloc_a6a0cc8156fe455996de64a9d05b1dfe = private unnamed_addr constant [184 x i8] c"unsafe precondition(s) violated: u32::unchecked_add cannot overflow\0A\0AThis indicates a bug in the program. This Undefined Behavior check is optional, and cannot be relied on for safety.", align 1
@anon.bf57a9b1e5c0ee841c3a09c7e52e3e2f.0 = private unnamed_addr constant <{ [8 x i8], [8 x i8] }> <{ [8 x i8] zeroinitializer, [8 x i8] undef }>, align 8
@alloc_facad3952d4c3e1cd7493775cc8b33f9 = private unnamed_addr constant [18 x i8] c"src/lib_simple.rs\00", align 1
@alloc_5a457ad608ce2912b4f582667f7c0aaf = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_facad3952d4c3e1cd7493775cc8b33f9, [16 x i8] c"\11\00\00\00\00\00\00\00\04\00\00\00\05\00\00\00" }>, align 8
@alloc_f2865b31a08be8224a16b427965f63b7 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_facad3952d4c3e1cd7493775cc8b33f9, [16 x i8] c"\11\00\00\00\00\00\00\00\15\00\00\00\1C\00\00\00" }>, align 8
@alloc_9bb4e171e3b404eeebfdd91f4134c9e4 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_facad3952d4c3e1cd7493775cc8b33f9, [16 x i8] c"\11\00\00\00\00\00\00\00\09\00\00\00\05\00\00\00" }>, align 8

; <core::ops::range::RangeInclusive<T> as core::iter::range::RangeInclusiveIteratorImpl>::spec_next
; Function Attrs: inlinehint nonlazybind uwtable
define { i32, i32 } @"_ZN107_$LT$core..ops..range..RangeInclusive$LT$T$GT$$u20$as$u20$core..iter..range..RangeInclusiveIteratorImpl$GT$9spec_next17hcd0000c708bd5d2aE"(ptr align 4 %self) unnamed_addr #0 {
start:
  %_6 = alloca [4 x i8], align 4
  %_0 = alloca [8 x i8], align 4
  %0 = getelementptr inbounds i8, ptr %self, i64 8
  %1 = load i8, ptr %0, align 4
  %_10 = trunc nuw i8 %1 to i1
  br i1 %_10, label %bb9, label %bb10

bb10:                                             ; preds = %start
  %_13 = getelementptr inbounds i8, ptr %self, i64 4
  %_3.i = load i32, ptr %self, align 4
  %_4.i = load i32, ptr %_13, align 4
  %_0.i = icmp ule i32 %_3.i, %_4.i
  %_2 = xor i1 %_0.i, true
  br i1 %_2, label %bb1, label %bb2

bb9:                                              ; preds = %start
  br label %bb1

bb2:                                              ; preds = %bb10
  %_5 = getelementptr inbounds i8, ptr %self, i64 4
  %_3.i1 = load i32, ptr %self, align 4
  %_4.i2 = load i32, ptr %_5, align 4
  %_0.i3 = icmp ult i32 %_3.i1, %_4.i2
  br i1 %_0.i3, label %bb4, label %bb6

bb1:                                              ; preds = %bb9, %bb10
  store i32 0, ptr %_0, align 4
  br label %bb8

bb6:                                              ; preds = %bb2
  %2 = getelementptr inbounds i8, ptr %self, i64 8
  store i8 1, ptr %2, align 4
  %3 = load i32, ptr %self, align 4
  store i32 %3, ptr %_6, align 4
  br label %bb7

bb4:                                              ; preds = %bb2
  %_8 = load i32, ptr %self, align 4
; call <u32 as core::iter::range::Step>::forward_unchecked
  %n = call i32 @"_ZN47_$LT$u32$u20$as$u20$core..iter..range..Step$GT$17forward_unchecked17h8bf83bce3ccab904E"(i32 %_8, i64 1)
  %4 = load i32, ptr %self, align 4
  store i32 %4, ptr %_6, align 4
  store i32 %n, ptr %self, align 4
  br label %bb7

bb7:                                              ; preds = %bb4, %bb6
  %5 = load i32, ptr %_6, align 4
  %6 = getelementptr inbounds i8, ptr %_0, i64 4
  store i32 %5, ptr %6, align 4
  store i32 1, ptr %_0, align 4
  br label %bb8

bb8:                                              ; preds = %bb1, %bb7
  %7 = load i32, ptr %_0, align 4
  %8 = getelementptr inbounds i8, ptr %_0, i64 4
  %9 = load i32, ptr %8, align 4
  %10 = insertvalue { i32, i32 } poison, i32 %7, 0
  %11 = insertvalue { i32, i32 } %10, i32 %9, 1
  ret { i32, i32 } %11
}

; <u32 as core::iter::range::Step>::forward_unchecked
; Function Attrs: inlinehint nonlazybind uwtable
define internal i32 @"_ZN47_$LT$u32$u20$as$u20$core..iter..range..Step$GT$17forward_unchecked17h8bf83bce3ccab904E"(i32 %start1, i64 %n) unnamed_addr #0 {
start:
  %rhs = trunc i64 %n to i32
  br label %bb1

bb1:                                              ; preds = %start
; call core::num::<impl u32>::unchecked_add::precondition_check
  call void @"_ZN4core3num21_$LT$impl$u20$u32$GT$13unchecked_add18precondition_check17hbd5cf8ded9e8b6fbE"(i32 %start1, i32 %rhs, ptr align 8 @alloc_f6c93850c917906f08a9412dbf717571) #7
  br label %bb2

bb2:                                              ; preds = %bb1
  %_0 = add nuw i32 %start1, %rhs
  ret i32 %_0
}

; core::num::<impl u32>::unchecked_add::precondition_check
; Function Attrs: inlinehint nounwind nonlazybind uwtable
define internal void @"_ZN4core3num21_$LT$impl$u20$u32$GT$13unchecked_add18precondition_check17hbd5cf8ded9e8b6fbE"(i32 %lhs, i32 %rhs, ptr align 8 %0) unnamed_addr #1 {
start:
  %_8 = alloca [16 x i8], align 8
  %_6 = alloca [48 x i8], align 8
  %_4.0 = add i32 %lhs, %rhs
  %_4.1 = icmp ult i32 %_4.0, %lhs
  br i1 %_4.1, label %bb1, label %bb2

bb2:                                              ; preds = %start
  ret void

bb1:                                              ; preds = %start
  %1 = getelementptr inbounds nuw { ptr, i64 }, ptr %_8, i64 0
  store ptr @alloc_a6a0cc8156fe455996de64a9d05b1dfe, ptr %1, align 8
  %2 = getelementptr inbounds i8, ptr %1, i64 8
  store i64 184, ptr %2, align 8
  store ptr %_8, ptr %_6, align 8
  %3 = getelementptr inbounds i8, ptr %_6, i64 8
  store i64 1, ptr %3, align 8
  %4 = load ptr, ptr @anon.bf57a9b1e5c0ee841c3a09c7e52e3e2f.0, align 8
  %5 = load i64, ptr getelementptr inbounds (i8, ptr @anon.bf57a9b1e5c0ee841c3a09c7e52e3e2f.0, i64 8), align 8
  %6 = getelementptr inbounds i8, ptr %_6, i64 32
  store ptr %4, ptr %6, align 8
  %7 = getelementptr inbounds i8, ptr %6, i64 8
  store i64 %5, ptr %7, align 8
  %8 = getelementptr inbounds i8, ptr %_6, i64 16
  store ptr inttoptr (i64 8 to ptr), ptr %8, align 8
  %9 = getelementptr inbounds i8, ptr %8, i64 8
  store i64 0, ptr %9, align 8
; call core::panicking::panic_nounwind_fmt
  call void @_ZN4core9panicking18panic_nounwind_fmt17h622822847ebd61beE(ptr align 8 %_6, i1 zeroext false, ptr align 8 %0) #8
  unreachable
}

; core::ops::range::RangeInclusive<Idx>::new
; Function Attrs: inlinehint nonlazybind uwtable
define void @"_ZN4core3ops5range25RangeInclusive$LT$Idx$GT$3new17haa39a513b85036e9E"(ptr sret([12 x i8]) align 4 %_0, i32 %start1, i32 %end) unnamed_addr #0 {
start:
  store i32 %start1, ptr %_0, align 4
  %0 = getelementptr inbounds i8, ptr %_0, i64 4
  store i32 %end, ptr %0, align 4
  %1 = getelementptr inbounds i8, ptr %_0, i64 8
  store i8 0, ptr %1, align 4
  ret void
}

; core::iter::range::<impl core::iter::traits::iterator::Iterator for core::ops::range::RangeInclusive<A>>::next
; Function Attrs: inlinehint nonlazybind uwtable
define { i32, i32 } @"_ZN4core4iter5range110_$LT$impl$u20$core..iter..traits..iterator..Iterator$u20$for$u20$core..ops..range..RangeInclusive$LT$A$GT$$GT$4next17hebd4af06e09a3c79E"(ptr align 4 %self) unnamed_addr #0 {
start:
; call <core::ops::range::RangeInclusive<T> as core::iter::range::RangeInclusiveIteratorImpl>::spec_next
  %0 = call { i32, i32 } @"_ZN107_$LT$core..ops..range..RangeInclusive$LT$T$GT$$u20$as$u20$core..iter..range..RangeInclusiveIteratorImpl$GT$9spec_next17hcd0000c708bd5d2aE"(ptr align 4 %self)
  %_0.0 = extractvalue { i32, i32 } %0, 0
  %_0.1 = extractvalue { i32, i32 } %0, 1
  %1 = insertvalue { i32, i32 } poison, i32 %_0.0, 0
  %2 = insertvalue { i32, i32 } %1, i32 %_0.1, 1
  ret { i32, i32 } %2
}

; <I as core::iter::traits::collect::IntoIterator>::into_iter
; Function Attrs: inlinehint nonlazybind uwtable
define void @"_ZN63_$LT$I$u20$as$u20$core..iter..traits..collect..IntoIterator$GT$9into_iter17h72288dca4ab69a75E"(ptr sret([12 x i8]) align 4 %_0, ptr align 4 %self) unnamed_addr #0 {
start:
  call void @llvm.memcpy.p0.p0.i64(ptr align 4 %_0, ptr align 4 %self, i64 12, i1 false)
  ret void
}

; Function Attrs: nonlazybind uwtable
define i32 @add(i32 %a, i32 %b) unnamed_addr #2 {
start:
  %0 = call { i32, i1 } @llvm.sadd.with.overflow.i32(i32 %a, i32 %b)
  %_3.0 = extractvalue { i32, i1 } %0, 0
  %_3.1 = extractvalue { i32, i1 } %0, 1
  br i1 %_3.1, label %panic, label %bb1

bb1:                                              ; preds = %start
  ret i32 %_3.0

panic:                                            ; preds = %start
; call core::panicking::panic_const::panic_const_add_overflow
  call void @_ZN4core9panicking11panic_const24panic_const_add_overflow17h813bff2d249a139bE(ptr align 8 @alloc_5a457ad608ce2912b4f582667f7c0aaf) #9
  unreachable
}

; Function Attrs: nonlazybind uwtable
define i32 @fibonacci(i32 %n) unnamed_addr #2 {
start:
  %iter = alloca [12 x i8], align 4
  %_5 = alloca [12 x i8], align 4
  %_4 = alloca [12 x i8], align 4
  %b = alloca [4 x i8], align 4
  %a = alloca [4 x i8], align 4
  %_0 = alloca [4 x i8], align 4
  switch i32 %n, label %bb1 [
    i32 0, label %bb3
    i32 1, label %bb2
  ]

bb1:                                              ; preds = %start
  store i32 0, ptr %a, align 4
  store i32 1, ptr %b, align 4
; call core::ops::range::RangeInclusive<Idx>::new
  call void @"_ZN4core3ops5range25RangeInclusive$LT$Idx$GT$3new17haa39a513b85036e9E"(ptr sret([12 x i8]) align 4 %_5, i32 2, i32 %n)
; call <I as core::iter::traits::collect::IntoIterator>::into_iter
  call void @"_ZN63_$LT$I$u20$as$u20$core..iter..traits..collect..IntoIterator$GT$9into_iter17h72288dca4ab69a75E"(ptr sret([12 x i8]) align 4 %_4, ptr align 4 %_5)
  call void @llvm.memcpy.p0.p0.i64(ptr align 4 %iter, ptr align 4 %_4, i64 12, i1 false)
  br label %bb6

bb3:                                              ; preds = %start
  store i32 0, ptr %_0, align 4
  br label %bb12

bb2:                                              ; preds = %start
  store i32 1, ptr %_0, align 4
  br label %bb12

bb12:                                             ; preds = %bb10, %bb2, %bb3
  %0 = load i32, ptr %_0, align 4
  ret i32 %0

bb6:                                              ; preds = %bb11, %bb1
; call core::iter::range::<impl core::iter::traits::iterator::Iterator for core::ops::range::RangeInclusive<A>>::next
  %1 = call { i32, i32 } @"_ZN4core4iter5range110_$LT$impl$u20$core..iter..traits..iterator..Iterator$u20$for$u20$core..ops..range..RangeInclusive$LT$A$GT$$GT$4next17hebd4af06e09a3c79E"(ptr align 4 %iter)
  %_7.0 = extractvalue { i32, i32 } %1, 0
  %_7.1 = extractvalue { i32, i32 } %1, 1
  %_9 = zext i32 %_7.0 to i64
  %2 = trunc nuw i64 %_9 to i1
  br i1 %2, label %bb9, label %bb10

bb9:                                              ; preds = %bb6
  %_11 = load i32, ptr %a, align 4
  %_12 = load i32, ptr %b, align 4
  %_13.0 = add i32 %_11, %_12
  %_13.1 = icmp ult i32 %_13.0, %_11
  br i1 %_13.1, label %panic, label %bb11

bb10:                                             ; preds = %bb6
  %3 = load i32, ptr %b, align 4
  store i32 %3, ptr %_0, align 4
  br label %bb12

bb11:                                             ; preds = %bb9
  %_14 = load i32, ptr %b, align 4
  store i32 %_14, ptr %a, align 4
  store i32 %_13.0, ptr %b, align 4
  br label %bb6

panic:                                            ; preds = %bb9
; call core::panicking::panic_const::panic_const_add_overflow
  call void @_ZN4core9panicking11panic_const24panic_const_add_overflow17h813bff2d249a139bE(ptr align 8 @alloc_f2865b31a08be8224a16b427965f63b7) #9
  unreachable

bb8:                                              ; No predecessors!
  unreachable
}

; Function Attrs: nonlazybind uwtable
define i32 @multiply(i32 %a, i32 %b) unnamed_addr #2 {
start:
  %0 = call { i32, i1 } @llvm.smul.with.overflow.i32(i32 %a, i32 %b)
  %_3.0 = extractvalue { i32, i1 } %0, 0
  %_3.1 = extractvalue { i32, i1 } %0, 1
  br i1 %_3.1, label %panic, label %bb1

bb1:                                              ; preds = %start
  ret i32 %_3.0

panic:                                            ; preds = %start
; call core::panicking::panic_const::panic_const_mul_overflow
  call void @_ZN4core9panicking11panic_const24panic_const_mul_overflow17h865155b80b7b9ba2E(ptr align 8 @alloc_9bb4e171e3b404eeebfdd91f4134c9e4) #9
  unreachable
}

; core::panicking::panic_nounwind_fmt
; Function Attrs: cold noinline noreturn nounwind nonlazybind uwtable
declare void @_ZN4core9panicking18panic_nounwind_fmt17h622822847ebd61beE(ptr align 8, i1 zeroext, ptr align 8) unnamed_addr #3

; Function Attrs: nocallback nofree nounwind willreturn memory(argmem: readwrite)
declare void @llvm.memcpy.p0.p0.i64(ptr noalias writeonly captures(none), ptr noalias readonly captures(none), i64, i1 immarg) #4

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare { i32, i1 } @llvm.sadd.with.overflow.i32(i32, i32) #5

; core::panicking::panic_const::panic_const_add_overflow
; Function Attrs: cold noinline noreturn nonlazybind uwtable
declare void @_ZN4core9panicking11panic_const24panic_const_add_overflow17h813bff2d249a139bE(ptr align 8) unnamed_addr #6

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare { i32, i1 } @llvm.smul.with.overflow.i32(i32, i32) #5

; core::panicking::panic_const::panic_const_mul_overflow
; Function Attrs: cold noinline noreturn nonlazybind uwtable
declare void @_ZN4core9panicking11panic_const24panic_const_mul_overflow17h865155b80b7b9ba2E(ptr align 8) unnamed_addr #6

attributes #0 = { inlinehint nonlazybind uwtable "probe-stack"="inline-asm" "target-cpu"="x86-64" }
attributes #1 = { inlinehint nounwind nonlazybind uwtable "probe-stack"="inline-asm" "target-cpu"="x86-64" }
attributes #2 = { nonlazybind uwtable "probe-stack"="inline-asm" "target-cpu"="x86-64" }
attributes #3 = { cold noinline noreturn nounwind nonlazybind uwtable "probe-stack"="inline-asm" "target-cpu"="x86-64" }
attributes #4 = { nocallback nofree nounwind willreturn memory(argmem: readwrite) }
attributes #5 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #6 = { cold noinline noreturn nonlazybind uwtable "probe-stack"="inline-asm" "target-cpu"="x86-64" }
attributes #7 = { nounwind }
attributes #8 = { noreturn nounwind }
attributes #9 = { noreturn }

!llvm.module.flags = !{!0, !1}
!llvm.ident = !{!2}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{i32 2, !"RtLibUseGOT", i32 1}
!2 = !{!"rustc version 1.91.1 (ed61e7d7e 2025-11-07)"}

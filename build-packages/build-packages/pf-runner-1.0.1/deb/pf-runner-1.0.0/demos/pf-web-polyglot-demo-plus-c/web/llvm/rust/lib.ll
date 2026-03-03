; ModuleID = 'lib_simple.78fb44681ef70933-cgu.0'
source_filename = "lib_simple.78fb44681ef70933-cgu.0"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: mustprogress nofree norecurse nosync nounwind nonlazybind willreturn memory(none) uwtable
define noundef i32 @add(i32 noundef %a, i32 noundef %b) unnamed_addr #0 {
start:
  %_0 = add i32 %b, %a
  ret i32 %_0
}

; Function Attrs: nofree norecurse nosync nounwind nonlazybind memory(none) uwtable
define noundef i32 @fibonacci(i32 noundef %n) unnamed_addr #1 {
start:
  %switch = icmp ult i32 %n, 2
  br i1 %switch, label %bb8, label %bb2.i

bb8:                                              ; preds = %bb2.i, %start
  %b.sroa.0.0 = phi i32 [ %n, %start ], [ %temp, %bb2.i ]
  ret i32 %b.sroa.0.0

bb2.i:                                            ; preds = %start, %bb2.i
  %b.sroa.0.113 = phi i32 [ %temp, %bb2.i ], [ 1, %start ]
  %a.sroa.0.012 = phi i32 [ %b.sroa.0.113, %bb2.i ], [ 0, %start ]
  %iter.sroa.0.011 = phi i32 [ %spec.select9, %bb2.i ], [ 2, %start ]
  %_0.i3.i = icmp uge i32 %iter.sroa.0.011, %n
  %not._0.i3.i = xor i1 %_0.i3.i, true
  %_0.i4.i = zext i1 %not._0.i3.i to i32
  %spec.select9 = add nuw i32 %iter.sroa.0.011, %_0.i4.i
  %temp = add i32 %b.sroa.0.113, %a.sroa.0.012
  %_0.i.not.i = icmp ugt i32 %spec.select9, %n
  %or.cond = select i1 %_0.i3.i, i1 true, i1 %_0.i.not.i
  br i1 %or.cond, label %bb8, label %bb2.i
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind nonlazybind willreturn memory(none) uwtable
define noundef i32 @multiply(i32 noundef %a, i32 noundef %b) unnamed_addr #0 {
start:
  %_0 = mul i32 %b, %a
  ret i32 %_0
}

attributes #0 = { mustprogress nofree norecurse nosync nounwind nonlazybind willreturn memory(none) uwtable "probe-stack"="inline-asm" "target-cpu"="x86-64" }
attributes #1 = { nofree norecurse nosync nounwind nonlazybind memory(none) uwtable "probe-stack"="inline-asm" "target-cpu"="x86-64" }

!llvm.module.flags = !{!0, !1}
!llvm.ident = !{!2}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{i32 2, !"RtLibUseGOT", i32 1}
!2 = !{!"rustc version 1.93.0 (254b59607 2026-01-19)"}

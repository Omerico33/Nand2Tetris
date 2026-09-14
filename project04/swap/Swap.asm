// This file is part of nand2tetris, as taught in The Hebrew University, and
// was written by Aviv Yaish. It is an extension to the specifications given
// [here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
// as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
// Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

// The program should swap between the max. and min. elements of an array.
// Assumptions:
// - The array's start address is stored in R14, and R15 contains its length
// - Each array value x is between -16384 < x < 16384
// - The address in R14 is at least >= 2048
// - R14 + R15 <= 16383
//
// Requirements:
// - Changing R14, R15 is not allowed.

// minind represent the index of the minimal element.
// maxind represent the index of the maximal element.
// i represent the index of the current element starting at the beginning of
// the array (i.e. i starts with RAM[R14]).
// end represent the end of the array.
// tmp is used to store one of the elements during the swap.
   // RAM[i] <- RAM[R14]
   @R14
   D=M
   @i
   M=D
   // RAM[end] <- RAM[R14] + RAM[R15]
   @R15
   D=D+M
   @end
   M=D
   @i
   D=M
   // Set RAM[minind], RAM[maxind] to be the index of the first element.
   @minind
   M=D
   @maxind
   M=D
   // i++
   @i
   M=M+1
(LOOP)
   // Continue while i < end.
   D=M
   @end
   D=D-M
   @END
   D;JEQ
   @i
   A=M
   D=M
   @minind
   A=M
   D=D-M
   @NOTMIN
   D;JGE
   // If A[minind] > A[i] then minind = i.
   @i
   D=M
   @minind
   M=D
(NOTMIN)
   @i
   A=M
   D=M
   @maxind
   A=M
   D=D-M
   @NOTMAX
   D;JLE
   // if A[maxind] < A[i] then maxind = i.
   @i
   D=M
   @maxind
   M=D
(NOTMAX)
   // i++
   @i
   M=M+1
   @LOOP
   0;JMP
(END)
   // A[minind] <-> A[maxind]
   @minind
   A=M
   D=M
   @tmp
   M=D
   @maxind
   A=M
   D=M
   @minind
   A=M
   M=D
   @tmp
   D=M
   @maxind
   A=M
   M=D
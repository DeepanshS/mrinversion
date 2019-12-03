// -*- coding: utf-8 -*-
//
//  array.h
//
//  Created by Deepansh J. Srivastava, Apr 11, 2019
//  Contact email = deepansh2012@gmail.com
//

#include <stdlib.h> // to use calloc, malloc, and free methods

// allocate memory for array of size m for a given type.
#define malloc_complex128(m) (complex128 *)malloc(m * sizeof(complex128))
#define malloc_complex64(m) (complex64 *)malloc(m * sizeof(complex64))
#define malloc_float(m) (float *)malloc(m * sizeof(float))
#define malloc_double(m) (double *)malloc(m * sizeof(double))
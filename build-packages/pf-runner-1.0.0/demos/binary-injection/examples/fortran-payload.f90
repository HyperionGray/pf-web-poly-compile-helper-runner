module injection_payload
    use iso_c_binding
    implicit none
    
contains
    
    ! Constructor-like subroutine (called via C wrapper)
    subroutine injected_fortran_constructor() bind(c, name="injected_fortran_constructor")
        write(*,*) '[INJECTED] Fortran payload constructor executed!'
        write(*,*) '[INJECTED] Fortran injection successful!'
    end subroutine injected_fortran_constructor
    
    ! Example function that can be called from injected code
    subroutine injected_fortran_function() bind(c, name="injected_fortran_function")
        write(*,*) '[INJECTED] Fortran function called from injection!'
    end subroutine injected_fortran_function
    
    ! Mathematical computation example
    function fortran_compute(x) result(y) bind(c, name="fortran_compute")
        real(c_double), intent(in) :: x
        real(c_double) :: y
        
        y = x * x + 2.0_c_double * x + 1.0_c_double
        write(*,*) '[INJECTED] Fortran computed:', x, '->', y
    end function fortran_compute
    
end module injection_payload

! C wrapper for constructor (since Fortran doesn't have __attribute__((constructor)))
! This would need to be compiled separately or included in a C file
!
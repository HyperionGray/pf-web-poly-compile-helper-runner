module injection_module
    use iso_c_binding
    implicit none
    
contains
    
    ! Constructor-like subroutine
    subroutine injected_constructor() bind(c, name="injected_constructor")
        write(*,*) '[INJECTED] Fortran constructor executed!'
        ! Add your injection code here
    end subroutine injected_constructor
    
    ! Example function
    subroutine injected_function() bind(c, name="injected_function")
        write(*,*) '[INJECTED] Fortran function called!'
    end subroutine injected_function
    
end module injection_module

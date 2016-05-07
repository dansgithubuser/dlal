#include "../include/simple_fft/fft_settings.h"

#ifdef __USE_SQUARE_BRACKETS_FOR_ELEMENT_ACCESS_OPERATOR
#undef __USE_SQUARE_BRACKETS_FOR_ELEMENT_ACCESS_OPERATOR
#endif

#include "../include/simple_fft/fft.h"
#include "test_fft.h"
#include <iostream>
#include <blitz/array.h>

namespace simple_fft {
namespace fft_test {

int testBlitz()
{
    std::cout << "Testing FFT algorithms with blitz" << std::endl;

    using namespace pulse_params;

    std::vector<real_type> t, x, y;
    makeGridsForPulse3D(t, x, y);

    // typedefing arrays
    typedef blitz::Array<real_type,int(1)> RealArray1D;
    typedef blitz::Array<complex_type,int(1)> ComplexArray1D;
    typedef blitz::Array<real_type,int(2)> RealArray2D;
    typedef blitz::Array<complex_type,int(2)> ComplexArray2D;
    typedef blitz::Array<real_type,int(3)> RealArray3D;
    typedef blitz::Array<complex_type,int(3)> ComplexArray3D;

    // 1D fields and spectrum
    RealArray1D E1_real(nt);
    ComplexArray1D E1_complex(nt), G1(nt), E1_restored(nt);

    // 2D fields and spectrum,
    RealArray2D E2_real(nt,nx);
    ComplexArray2D E2_complex(nt,nx), G2(nt,nx), E2_restored(nt,nx);

    // 3D fields and spectrum
    RealArray3D E3_real(nt,nx,ny);
    ComplexArray3D E3_complex(nt,nx,ny), G3(nt,nx,ny), E3_restored(nt,nx,ny);

    if (!commonPartsForTests3D(E1_real, E2_real, E3_real, E1_complex, E2_complex,
                               E3_complex, G1, G2, G3, E1_restored, E2_restored,
                               E3_restored, t, x, y))
    {
        std::cout << "Tests of FFT with blitz++ arrays returned with errors!" << std::endl;
        return FAILURE;
    }

    std::cout << "Tests of FFT with blitz++ arrays completed successfully!" << std::endl;
    return SUCCESS;
}

} // namespace fft_test
} // namespace simple_fft

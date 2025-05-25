#include <vtkMath.h>
#include <cassert>
#include <cstdlib>

int main()
{
    double pi = vtkMath::Pi();
    assert(pi > 3.14 && pi < 3.15);

    double v[3] = {1.0, 2.0, 3.0};
    vtkMath::Normalize(v);
    double len = std::sqrt(vtkMath::Dot(v, v));
    assert(std::abs(len - 1.0) < 1e-6);

    return EXIT_SUCCESS;
}
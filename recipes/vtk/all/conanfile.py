from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import copy, get, apply_conandata_patches, export_conandata_patches, collect_libs
from conan.tools.scm import Version
from conan.errors import ConanException
import os

class VTKConan(ConanFile):
    name = "vtk"
    license = "BSD 3-clause License"
    url = "https://github.com/Kitware/VTK"
    description = (
        "VTK is an open-source software system for image processing, 3D graphics,"
        "volume rendering and visualization"
    )
    topics = (
        "vtk", "visualization", "graphics", "rendering", "volume-rendering",
        "imaging", "medical-imaging", "mesh", "point-cloud", "geometry",
        "data-analysis", "pipeline", "C++", "python", "cross-platform",
        "3d", "openGL", "simulation", "scientific-computing"
    )
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "use_qt": [True, False],
        "use_cuda": [True, False],
        "cuda_arch_bin": [None, "ANY"],
        "rendering": [True, False],
        "io": [True, False],
        "imaging": [True, False],
        "mesh": [True, False],
        "parallel": [True, False],
        "thirdparty": [True, False],
        "tests": [True, False],
        "legacy": [True, False]
    }
    default_options = {
        "shared": False,
        "use_qt": False,
        "use_cuda": False,
        "cuda_arch_bin": None,
        "rendering": True,
        "io": True,
        "imaging": True,
        "mesh": True,
        "parallel": False,
        "thirdparty": True,
        "legacy": False,
        "tests": False
    }
    
    def validate_cuda_arch_bin(self):
        raw = self.options.cuda_arch_bin
        if not raw:
            raise ConanException("cuda_arch_bin must be set when use_cuda=True")
        pattern = re.compile(r"^\d+\.\d+(;\d+\.\d+)*$")
        if not pattern.match(str(raw)):
            raise ConanException(
                f"Bad format for cuda_arch_bin: {raw!r}, use e.g. '5.1;6.0;7.5'"
            )
            
        for arch in str(raw).split(";"):
            val = float(arch)
            if val < 5.0 or val > 9.0:
                raise ConanException(
                    f"cuda_arch_bin values must be between 5.0 and 9.0, got {val}"
                )
        self.output.info(f"Validated CUDA_ARCH_BIN = {raw}")  

    def validate(self):
        if self.options.use_cuda: 
            self.validate_cuda_arch_bin()

    def requirements(self):
        self.requires("zlib/[>=1.3.1 <2]")
        self.requires("eigen/[>=3.4.0 <4]")
        if self.options.use_qt:
            self.requires("qt/[>=6.7.3 <7]")
        #TODO: OSMESA libraries?
    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def export_sources(self):
        export_conandata_patches(self)

    def generate(self):
        # Dependencies
        deps = CMakeDeps(self)
        deps.set_property("eigen", "cmake_file_name", "Eigen3")
        deps.set_property("eigen", "cmake_target_name", "Eigen3::Eigen3")
        deps.generate()

        tc = CMakeToolchain(self)
        
        # remove Conan's default runtime block
        tc.blocks.remove("vs_runtime")

        # General VTK settings
        tc.variables["BUILD_PERF_TESTS"] = "ON" if self.options.tests else "OFF"
        tc.variables["VTK_LEGACY_REMOVE"] = "ON" if self.options.legacy else "OFF"
        tc.variables["VTK_USE_CUDA"] = "ON" if self.options.use_cuda else "OFF"
        tc.variables["VTK_MODULE_USE_EXTERNAL_VTK_eigen"] = "ON"

        # Module groups controlled by options
        tc.variables["VTK_Group_Rendering"] = "ON" if self.options.rendering else "OFF"
        tc.variables["VTK_Group_IO"] = "ON" if self.options.io else "OFF"
        tc.variables["VTK_Group_Imaging"] = "ON" if self.options.imaging else "OFF"
        tc.variables["VTK_Group_Mesh"] = "ON" if self.options.mesh else "OFF"
        tc.variables["VTK_Group_Parallel"] = "ON" if self.options.parallel else "OFF"
        tc.variables["VTK_Group_ThirdParty"] = "ON" if self.options.thirdparty else "OFF"

        # Qt support
        tc.variables["VTK_GROUP_ENABLE_Qt"] = "YES" if self.options.use_qt else "NO"
        for module in [
            "VTK_GUISupportQt",
            "VTK_RenderingQt",
            "VTK_ViewsQt",
            "VTK_GUISupportQtQuick",
            "VTK_GUISupportQtSQL",
        ]:
            tc.variables[f"VTK_MODULE_ENABLE_{module}"] = "YES" if self.options.use_qt else "NO"

        # CUDA architecture
        if self.options.cuda_arch_bin:
            tc.variables["CUDA_ARCH_BIN"] = self.options.cuda_arch_bin

        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "VTK")
        self.cpp_info.set_property("cmake_target_name", "VTK::VTK")
        self.cpp_info.set_property("pkg_config_name", "VTK")
        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.bindirs = ["bin"]
        
        ver = Version(self.version)
        self.cpp_info.includedirs = [f"include/vtk-{ver.major}.{ver.minor}"]
        
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["opengl32", "Psapi", "Dbghelp"]
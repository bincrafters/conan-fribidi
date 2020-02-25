from conans import ConanFile, Meson, tools
import glob
import os
import shutil


class FribidiConan(ConanFile):
    name = "fribidi"
    version = "1.0.5"
    description = "Keep it short"
    # topics can get used for searches, GitHub topics, Bintray tags etc. Add here keywords about the library
    topics = ("conan", "fribidi", "unicode","bidi","text")
    url = "https://github.com/bincrafters/conan-fribidi"
    homepage = "https://github.com/fribidi/fribidi"
    license = "LGPL-2.1"  # Indicates license type of the packaged library; please use SPDX Identifiers https://spdx.org/licenses/
    exports = ["LICENSE.md"]      # Packages the license for the conanfile.py
    # Remove following lines if the target lib does not use cmake.
    generators = "pkg_config"

    # Options may need to change depending on the packaged library.
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    # Custom attributes for Bincrafters recipe conventions
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC


    def build_requirements(self):
        if not tools.which("pkg-config"):
            self.build_requires("pkg-config_installer/0.29.2@bincrafters/stable")
        if not tools.which("meson"):
            self.build_requires("meson/0.53.0")

    def source(self):
        tools.get("https://github.com/fribidi/fribidi/releases/download/v{0}/fribidi-{0}.tar.bz2".format(self.version), 
                    sha256="6a64f2a687f5c4f203a46fa659f43dd43d1f8b845df8d723107e8a7e6158e4ce")
        extracted_dir = self.name + "-" + self.version

        # Rename to "source_subfolder" is a convention to simplify later steps
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_meson(self):
        defs = dict()
        defs["docs"] = "false"

        meson = Meson(self)
        meson.configure(build_folder="build", source_folder=self._source_subfolder, defs=defs)
        return meson

    def build(self):
        tools.replace_in_file(os.path.join(self._source_subfolder, "meson.build"), "subdir('bin')", "")
        tools.replace_in_file(os.path.join(self._source_subfolder, "meson.build"), "subdir('test')", "")
        meson = self._configure_meson()
        meson.build()

    def _fix_library_names(self, path):
        # regression in 1.16
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(path):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" % (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        meson = self._configure_meson()
        meson.install()

        self._fix_library_names(os.path.join(self.package_folder, "lib"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
    
    def package_info(self):
        if not self.options.shared:
            self.cpp_info.defines.append("FRIBIDI_STATIC=1")

        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "fribidi"))

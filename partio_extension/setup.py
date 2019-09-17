from distutils.core import setup, Extension
import platform

defs = []
cxx_args = []

defs.append(('PARTIO_USE_ZLIB', None))
						 
if platform.system() == 'Windows':
	defs.append(('PARTIO_WIN32', None))
	defs.append(('_USE_MATH_DEFINES', None))
elif platform.system() == 'Linux':
	cxx_args = ["-fPIC", "-w"]

module1 = Extension('_partio',
					include_dirs = ['../extern/partio/src/lib', '../extern/zlib/src'],
					define_macros = defs,
					extra_compile_args = cxx_args,
					sources = [
					'../extern/partio/src/lib/core/Particle.cpp',
					'../extern/partio/src/lib/core/ParticleCaching.cpp',
					'../extern/partio/src/lib/core/ParticleHeaders.cpp',
					'../extern/partio/src/lib/core/ParticleSimple.cpp',
					'../extern/partio/src/lib/core/ParticleSimpleInterleave.cpp',
					'../extern/partio/src/lib/io/BGEO.cpp',
					'../extern/partio/src/lib/io/BIN.cpp',
					'../extern/partio/src/lib/io/GEO.cpp',
					'../extern/partio/src/lib/io/MC.cpp',
					'../extern/partio/src/lib/io/ParticleIO.cpp',
					'../extern/partio/src/lib/io/PDA.cpp',
					'../extern/partio/src/lib/io/PDB.cpp',
					'../extern/partio/src/lib/io/PDC.cpp',
					'../extern/partio/src/lib/io/PRT.cpp',
					'../extern/partio/src/lib/io/PTC.cpp',
					'../extern/partio/src/lib/io/PTS.cpp',
					'../extern/partio/src/lib/io/RIB.cpp',
					'../extern/partio/src/lib/io/ZIP.cpp',
					'../extern/zlib/src/adler32.c',
					'../extern/zlib/src/compress.c',
					'../extern/zlib/src/crc32.c',
					'../extern/zlib/src/deflate.c',
					'../extern/zlib/src/gzio.c',
					'../extern/zlib/src/infback.c',
					'../extern/zlib/src/inffast.c',
					'../extern/zlib/src/inflate.c',
					'../extern/zlib/src/inftrees.c',
					'../extern/zlib/src/trees.c',
					'../extern/zlib/src/uncompr.c',
					'../extern/zlib/src/zutil.c',
					'partio_wrap.cxx'])
					
tst = setup (name = '_partio',
	version = '1.0',
	description = 'partio package',
	ext_modules = [module1])

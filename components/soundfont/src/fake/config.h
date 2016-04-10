#ifdef __APPLE__
#ifndef CONFIG_H
#define CONFIG_H

#define DARWIN 1

#define HAVE_ARPA_INET_H 1
#define HAVE_DLFCN_H 1
#define HAVE_ERRNO_H 1
#define HAVE_FCNTL_H 1
#define HAVE_INTTYPES_H 1
#define HAVE_LIBPTHREAD TRUE
#define HAVE_LIMITS_H 1
#define HAVE_MATH_H 1
#define HAVE_MEMORY_H 1
#define HAVE_NETINET_IN_H 1
#define HAVE_NETINET_TCP_H 1
#define HAVE_PTHREAD_H 1
#define HAVE_SIGNAL_H 1
#define HAVE_STDARG_H 1
#define HAVE_STDINT_H 1
#define HAVE_STDIO_H 1
#define HAVE_STDLIB_H 1
#define HAVE_STRINGS_H 1
#define HAVE_STRING_H 1
#define HAVE_SYS_IOCTL_H 1
#define HAVE_SYS_MMAN_H 1
#define HAVE_SYS_SOCKET_H 1
#define HAVE_SYS_STAT_H 1
#define HAVE_SYS_TIME_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_UNISTD_H 1
#define HAVE_GETOPT_H 1

#define IPV6 1

#define STDC_HEADERS 1

#define VERSION "0.0.0"

#define SUPPORTS_VLA 1

#ifndef __cplusplus
  #undef inline
#endif

#endif /* CONFIG_H */
#endif /* #ifdef __APPLE__ */

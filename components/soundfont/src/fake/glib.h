#ifndef GLIB_H_INCLUDED
#define GLIB_H_INCLUDED

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define TRUE 1
#define FALSE 0

#define PRETEND_POINTER (void*)0xdede

/*error*/
typedef struct{
	uint32_t domain;
	int code;
	char* message;
} GError;

static void g_clear_error(void* err){}

/*time*/
typedef struct{
	long tv_sec;
	long tv_usec;
} GTimeVal;

static void g_get_current_time(GTimeVal* result){ result->tv_sec=0; result->tv_usec=0; }

/*threads*/
typedef void* GThread;
typedef void* GThreadFunc;

static int g_thread_supported(){ return 0; }
static void g_thread_init(void* vtable){}
static void* g_thread_create(void* func, void* data, int joinable, void* error){ return PRETEND_POINTER; }
static void* g_thread_join(void* thread){ return PRETEND_POINTER; }

static void g_usleep(unsigned long microseconds){ printf("g_usleep called\n"); }

/*mutexes*/
#define G_STATIC_MUTEX_INIT PRETEND_POINTER

typedef void* GMutex;
typedef void* GRecMutex;
typedef void* GStaticMutex;
typedef void* GStaticRecMutex;

static void* g_mutex_new(){ return PRETEND_POINTER; }
static void g_mutex_free(void* mutex){}
static void g_mutex_lock(void* mutex){}
static void g_mutex_unlock(void* mutex){}
static void g_static_mutex_init(void* mutex){}
static void g_static_mutex_free(void* mutex){}
static void g_static_mutex_lock(void* mutex){}
static void g_static_mutex_unlock(void* mutex){}
static void g_static_rec_mutex_init(void* mutex){}
static void g_static_rec_mutex_free(void* mutex){}
static void g_static_rec_mutex_lock(void* mutex){}
static void g_static_rec_mutex_unlock(void* mutex){}

/*conditions*/
typedef void* GCond;

static void* g_cond_new(){ return PRETEND_POINTER; }
static void g_cond_free(void* cond){}
static void g_cond_signal(void* cond){}
static void g_cond_wait(void* cond, void* mutex){}
static void g_cond_broadcast(void* cond){}

/*atomic*/
static void g_atomic_int_set(volatile int* atomic, int newval){ *atomic=newval; }
static int g_atomic_int_get(const volatile int* atomic){ return *atomic; }
static int g_atomic_int_add(volatile int* atomic, int val){ int tmp=*atomic; *atomic+=val; return tmp; }
static int g_atomic_int_exchange_and_add(volatile int* atomic, int val){ return g_atomic_int_add(atomic, val); }
static void g_atomic_int_inc(int* atomic){ ++*atomic; }

/*private -- not to be confused with private members or asymmetric cryptography*/
typedef void* GStaticPrivate;

static void g_static_private_init(void* private_key){}
static void g_static_private_free(void* private_key){}
static void g_static_private_set(void* private_key, void* data, void* notify){}
static void* g_static_private_get(void* private_key){ return PRETEND_POINTER; }

/*g_newa*/
#if defined(__GNUC__)
	#undef alloca
	#define alloca(size) __builtin_alloca(size)
#else
	#if defined(_MSC_VER)||defined(__DMC__)
		#include <malloc.h>
		#define alloca _alloca
	#else
		#ifdef _AIX
			#pragma alloca
		#else
			#ifndef alloca
				extern "C" {
					char* alloca();
				}
			#endif
		#endif
	#endif
#endif

#define g_alloca(size) alloca(size)
#define g_newa(struct_type, n_structs) ((struct_type*)g_alloca(sizeof(struct_type)*(unsigned long)(n_structs)))

/*endianness*/
#define GUINT16_SWAP_LE_BE(val) ((guint16)(\
	(((guint16)(val)&(guint16)0x00ffu)<<8)|\
	(((guint16)(val)&(guint16)0xff00u)>>8)\
))
#define GUINT32_SWAP_LE_BE(val) ((guint32)(\
	(((guint32)(val)&(guint32)0x000000ffu)<<24)|\
	(((guint32)(val)&(guint32)0x0000ff00u)<< 8)|\
	(((guint32)(val)&(guint32)0x00ff0000u)>> 8)|\
	(((guint32)(val)&(guint32)0xff000000u)>>24)\
))

#if FLUID_IS_BIG_ENDIAN
	#define G_LITTLE_ENDIAN 1234
	#define G_BYTE_ORDER G_LITTLE_ENDIAN
	#define GINT16_TO_BE(val)    ((gint16) (val))
	#define GUINT16_TO_BE(val)   ((guint16) (val))
	#define GINT16_TO_BE(val)    ((gint16) GUINT16_SWAP_LE_BE (val))
	#define GUINT16_TO_BE(val)   (GUINT16_SWAP_LE_BE (val))
	#define GINT16_FROM_BE(val)  ((gint16) (val))
	#define GUINT16_FROM_BE(val) ((guint16) (val))
	#define GINT16_FROM_LE(val)  ((gint16) GUINT16_SWAP_LE_BE (val))
	#define GUINT16_FROM_LE(val) (GUINT16_SWAP_LE_BE (val))
	#define GINT32_TO_BE(val)    ((gint32) (val))
	#define GUINT32_TO_BE(val)   ((guint32) (val))
	#define GINT32_TO_LE(val)    ((gint32) GUINT32_SWAP_LE_BE (val))
	#define GUINT32_TO_LE(val)   (GUINT32_SWAP_LE_BE (val))
	#define GINT32_FROM_BE(val)  ((gint32) (val))
	#define GUINT32_FROM_BE(val) ((guint32) (val))
	#define GINT32_FROM_LE(val)  ((gint32) GUINT32_SWAP_LE_BE (val))
	#define GUINT32_FROM_LE(val) (GUINT32_SWAP_LE_BE (val))
#else
	#define G_BIG_ENDIAN 4321
	#define G_BYTE_ORDER G_BIG_ENDIAN
	#define GINT16_TO_LE(val)    ((gint16) (val))
	#define GUINT16_TO_LE(val)   ((guint16) (val))
	#define GINT16_TO_BE(val)    ((gint16) GUINT16_SWAP_LE_BE (val))
	#define GUINT16_TO_BE(val)   (GUINT16_SWAP_LE_BE (val))
	#define GINT16_FROM_LE(val)  ((gint16) (val))
	#define GUINT16_FROM_LE(val) ((guint16) (val))
	#define GINT16_FROM_BE(val)  ((gint16) GUINT16_SWAP_LE_BE (val))
	#define GUINT16_FROM_BE(val) (GUINT16_SWAP_LE_BE (val))
	#define GINT32_TO_LE(val)    ((gint32) (val))
	#define GUINT32_TO_LE(val)   ((guint32) (val))
	#define GINT32_TO_BE(val)    ((gint32) GUINT32_SWAP_LE_BE (val))
	#define GUINT32_TO_BE(val)   (GUINT32_SWAP_LE_BE (val))
	#define GINT32_FROM_LE(val)  ((gint32) (val))
	#define GUINT32_FROM_LE(val) ((guint32) (val))
	#define GINT32_FROM_BE(val)  ((gint32) GUINT32_SWAP_LE_BE (val))
	#define GUINT32_FROM_BE(val) (GUINT32_SWAP_LE_BE (val))
#endif

/*misc*/
#define G_STMT_START do
#define G_STMT_END   while(0)

#define g_return_val_if_fail
#define g_return_if_fail

#define GPOINTER_TO_INT(p) ((int)(long)(p))
#define GPOINTER_TO_UINT(p) ((unsigned)(long)(p))
#define GINT_TO_POINTER(i) ((void*)(long)(i))

typedef int gboolean;
typedef void* gpointer;
typedef int gint;
typedef unsigned guint;
typedef long glong;
typedef uint8_t guint8;
typedef int16_t gint16;
typedef int32_t gint32;
typedef uint32_t guint32;

static int g_snprintf(char* string, unsigned long n, char const* format, ...){ return 0; }
static int g_shell_parse_argv(const char* command_line, int* argcp, char*** argvp, void* error){ return 0; }
static void g_strfreev(void* str_array){}

#endif//GLIB_H_INCLUDED

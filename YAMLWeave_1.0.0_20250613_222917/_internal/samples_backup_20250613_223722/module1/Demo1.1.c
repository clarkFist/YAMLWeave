/**
 * 模块1示例文件1
 * 用于测试多文件场景下的插桩功能
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/**
 * 模块1函数1: 数据验证与边界检查
 */
int validate_data(int value) {
    // TC001 STEP1 segment1
    
    printf("验证数据: %d\n", value);
    
    // TC101 STEP1 segment1
    
    // TC201 STEP1 benchmark_start
    
    return value > 0 ? 1 : 0;
}

/**
 * 模块1函数2: 数据处理与转换
 */
void process_data(int data) {
    // TC001 STEP2 segment1
    
    printf("处理数据: %d\n", data);
    
    // TC102 STEP1 format_check
    
    // TC102 STEP1 segment1
    
    // TC102 STEP1 check_business_rules
}

/**
 * 模块1函数3: 系统初始化与资源分配
 */
int initialize_system(void* config) {
    // TC101 STEP1 log_init
    
    // TC101 STEP1 segment2
    
    printf("系统初始化中...\n");
    return 0;
}

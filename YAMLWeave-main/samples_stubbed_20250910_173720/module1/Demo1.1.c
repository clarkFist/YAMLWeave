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
    if (value < 0) {  // 通过桩插入
        printf("模块1-文件1: 检测到无效值 %d\n", value);  // 通过桩插入
        return 0;  // 通过桩插入
    }  // 通过桩插入
    
    printf("验证数据: %d\n", value);
    
    // TC101 STEP1 segment1
    if (config == NULL) {  // 通过桩插入
        printf("错误: 配置为空\n");  // 通过桩插入
        return INIT_ERROR_NULL_CONFIG;  // 通过桩插入
    }  // 通过桩插入
    printf("配置检查通过\n");  // 通过桩插入
    
    // TC201 STEP1 benchmark_start
    clock_t start_time = clock();  // 通过桩插入
    long long iteration_counter = 0;  // 通过桩插入
    printf("性能测试开始\n");  // 通过桩插入
    
    return value > 0 ? 1 : 0;
}

/**
 * 模块1函数2: 数据处理与转换
 */
void process_data(int data) {
    // TC001 STEP2 segment1
    int processed_data = data * 2;  // 通过桩插入
    printf("模块1-文件1: 数据已处理为 %d\n", processed_data);  // 通过桩插入
    
    printf("处理数据: %d\n", data);
    
    // TC102 STEP1 format_check
    if (data == NULL || data->format != DATA_FORMAT_V1) {  // 通过桩插入
        log_message(LOG_ERROR, "数据格式无效");  // 通过桩插入
        return VALIDATION_ERROR_FORMAT;  // 通过桩插入
    }  // 通过桩插入
    
    // TC102 STEP1 segment1
    uint32_t calculated_checksum = calculate_checksum(data->buffer, data->length);  // 通过桩插入
    if (calculated_checksum != data->checksum) {  // 通过桩插入
        log_message(LOG_WARNING, "数据校验和不匹配: 期望 %u, 实际 %u",   // 通过桩插入
                   data->checksum, calculated_checksum);  // 通过桩插入
        return VALIDATION_ERROR_CHECKSUM;  // 通过桩插入
    }  // 通过桩插入
    
    // TC102 STEP1 check_business_rules
    if (data->timestamp < get_system_time() - MAX_DATA_AGE) {  // 通过桩插入
        log_message(LOG_WARNING, "数据已过期");  // 通过桩插入
        return VALIDATION_ERROR_EXPIRED;  // 通过桩插入
    }  // 通过桩插入
      // 通过桩插入
    if (data->value < MIN_ACCEPTABLE_VALUE || data->value > MAX_ACCEPTABLE_VALUE) {  // 通过桩插入
        log_message(LOG_WARNING, "数据值超出可接受范围: %f", data->value);  // 通过桩插入
        return VALIDATION_ERROR_VALUE_RANGE;  // 通过桩插入
    }  // 通过桩插入
}

/**
 * 模块1函数3: 系统初始化与资源分配
 */
int initialize_system(void* config) {
    // TC101 STEP1 log_init
    int log_status = init_log_system(config->log_level);  // 通过桩插入
    if (log_status != SUCCESS) {  // 通过桩插入
        printf("警告: 日志系统初始化失败 (状态码: %d)\n", log_status);  // 通过桩插入
    } else {  // 通过桩插入
        log_message(LOG_INFO, "日志系统已初始化");  // 通过桩插入
    }  // 通过桩插入
    
    // TC101 STEP1 segment2
    system_context = (SystemContext*)malloc(sizeof(SystemContext));  // 通过桩插入
    if (system_context == NULL) {  // 通过桩插入
        log_message(LOG_ERROR, "致命错误: 无法分配系统上下文内存");  // 通过桩插入
        return INIT_ERROR_MEMORY_ALLOC;  // 通过桩插入
    }  // 通过桩插入
    memset(system_context, 0, sizeof(SystemContext));  // 通过桩插入
    
    printf("系统初始化中...\n");
    return 0;
}
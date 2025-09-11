/**
 * 模块2示例文件2
 * 用于测试多文件场景下的插桩功能
 */

#include <stdio.h>
#include <math.h>

/**
 * 模块2函数3: 处理原始数据
 */
float process_raw_data(int raw_data) {
    // TC002 STEP3 segment1
    
    printf("处理原始数据: %d\n", raw_data);
    return (float)raw_data * 1.5f;
}

/**
 * 模块2函数4: 验证结果
 */
int verify_result(float result, float expected) {
    // TC002 STEP4 segment1
    
    printf("验证结果: 实际 %.2f vs 期望 %.2f\n", result, expected);
    
    // TC202 STEP1 test_min_max
    
    return fabs(result - expected) < (expected * 0.05f) ? 1 : 0;
}

/**
 * 模块2函数5: 复杂数据处理
 */
void process_complex_data(void* data_array, int array_size) {
    // TC203 STEP1 complex_structures
    
    printf("处理复杂数据结构...\n");
}

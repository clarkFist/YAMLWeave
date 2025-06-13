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
    if (raw_data < 0) {  // 通过桩插入
        printf("模块2-文件2: 无效原始数据 %d\n", raw_data);  // 通过桩插入
        return 0.0f;  // 通过桩插入
    }  // 通过桩插入
    
    printf("处理原始数据: %d\n", raw_data);
    return (float)raw_data * 1.5f;
}

/**
 * 模块2函数4: 验证结果
 */
int verify_result(float result, float expected) {
    // TC002 STEP4 segment1
    float diff = result - expected;  // 通过桩插入
    float tolerance = expected * 0.05f;  // 通过桩插入
    printf("模块2-文件2: 差异 %.2f, 容差 %.2f\n", diff, tolerance);  // 通过桩插入
    
    printf("验证结果: 实际 %.2f vs 期望 %.2f\n", result, expected);
    
    // TC202 STEP1 test_min_max
    // 测试整型边界值  // 通过桩插入
    if (value == INT_MIN || value == INT_MAX) {  // 通过桩插入
        printf("检测到整型边界值: %d\n", value);  // 通过桩插入
        return BOUNDARY_CASE;  // 通过桩插入
    }  // 通过桩插入
      // 通过桩插入
    // 测试浮点数边界值  // 通过桩插入
    if (fabs(double_value) < 1e-10 || fabs(double_value) > 1e10) {  // 通过桩插入
        printf("检测到浮点数边界值: %e\n", double_value);  // 通过桩插入
        return BOUNDARY_CASE;  // 通过桩插入
    }  // 通过桩插入
    
    return fabs(result - expected) < (expected * 0.05f) ? 1 : 0;
}

/**
 * 模块2函数5: 复杂数据处理
 */
void process_complex_data(void* data_array, int array_size) {
    // TC203 STEP1 complex_structures
    // 多级嵌套的数据结构和控制流测试  // 通过桩插入
    for (int i = 0; i < array_size; i++) {  // 通过桩插入
        if (data_array[i].type == TYPE_COMPOSITE) {  // 通过桩插入
            CompositeData* composite = (CompositeData*)data_array[i].data;  // 通过桩插入
              // 通过桩插入
            for (int j = 0; j < composite->child_count; j++) {  // 通过桩插入
                ChildData* child = &composite->children[j];  // 通过桩插入
                  // 通过桩插入
                if (child->flags & FLAG_REQUIRES_PROCESSING) {  // 通过桩插入
                    switch (child->category) {  // 通过桩插入
                        case CATEGORY_A:  // 通过桩插入
                            process_category_a(child);  // 通过桩插入
                            break;  // 通过桩插入
                        case CATEGORY_B:  // 通过桩插入
                            if (child->priority > HIGH_PRIORITY) {  // 通过桩插入
                                process_high_priority_b(child);  // 通过桩插入
                            } else {  // 通过桩插入
                                process_normal_priority_b(child);  // 通过桩插入
                            }  // 通过桩插入
                            break;  // 通过桩插入
                        default:  // 通过桩插入
                            log_message(LOG_WARNING, "未知类别: %d", child->category);  // 通过桩插入
                            continue;  // 通过桩插入
                    }  // 通过桩插入
                      // 通过桩插入
                    // 统计处理结果  // 通过桩插入
                    processed_count++;  // 通过桩插入
                    total_size += child->size;  // 通过桩插入
                }  // 通过桩插入
            }  // 通过桩插入
        }  // 通过桩插入
    }  // 通过桩插入
      // 通过桩插入
    printf("处理完成: %d 项, 总大小: %lu 字节\n", processed_count, total_size);  // 通过桩插入
    
    printf("处理复杂数据结构...\n");
}
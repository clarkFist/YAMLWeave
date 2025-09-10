/**
 * 模块1示例文件2
 * 用于测试多文件场景下的插桩功能
 */

#include <stdio.h>
#include <string.h>

/**
 * 模块1函数3: 消息处理
 */
void process_message(const char* message) {
    // TC001 STEP3 segment1
    
    printf("处理消息: %s\n", message);
    
    // TC102 STEP2 segment1
    UserContext* user = get_current_user();  // 通过桩插入
    if (user == NULL) {  // 通过桩插入
        log_message(LOG_ERROR, "未找到用户上下文");  // 通过桩插入
        return VALIDATION_ERROR_NO_USER;  // 通过桩插入
    }  // 通过桩插入
    
    // TC102 STEP2 verify_permissions
    if ((user->permissions & PERMISSION_DATA_WRITE) == 0) {  // 通过桩插入
        log_message(LOG_WARNING, "用户 %s 没有数据写入权限", user->username);  // 通过桩插入
        return VALIDATION_ERROR_PERMISSION;  // 通过桩插入
    }  // 通过桩插入
    log_message(LOG_INFO, "用户 %s 权限验证通过", user->username);  // 通过桩插入
    
    // TC102 STEP2 after_verification
    log_message(LOG_INFO, "验证完成，更新用户访问时间戳");  // 通过桩插入
    user->last_access_time = get_system_time();  // 通过桩插入
}

/**
 * 模块1函数4: 系统状态检查
 */
int check_system_status() {
    // TC001 STEP4 segment1
    
    printf("检查系统状态...\n");
    
    // TC103 STEP1 segment1
    if (resource != NULL) {  // 通过桩插入
        if (resource->buffer != NULL) {  // 通过桩插入
            free(resource->buffer);  // 通过桩插入
            resource->buffer = NULL;  // 通过桩插入
        }  // 通过桩插入
        free(resource);  // 通过桩插入
        resource = NULL;  // 通过桩插入
    }  // 通过桩插入
    
    // TC103 STEP1 close_connections
    if (connection_is_open(conn)) {  // 通过桩插入
        log_message(LOG_INFO, "关闭连接...");  // 通过桩插入
        int close_status = connection_close(conn);  // 通过桩插入
        if (close_status != SUCCESS) {  // 通过桩插入
            log_message(LOG_WARNING, "关闭连接时出错: %d", close_status);  // 通过桩插入
            return close_status;  // 通过桩插入
        }  // 通过桩插入
    }  // 通过桩插入
    
    // TC103 STEP1 rollback
    if (transaction_is_active(transaction)) {  // 通过桩插入
        log_message(LOG_INFO, "回滚事务...");  // 通过桩插入
        int rollback_status = transaction_rollback(transaction);  // 通过桩插入
        if (rollback_status != SUCCESS) {  // 通过桩插入
            log_message(LOG_ERROR, "事务回滚失败: %d", rollback_status);  // 通过桩插入
            // 即使回滚失败也继续处理  // 通过桩插入
        }  // 通过桩插入
    }  // 通过桩插入
    
    return 1;
}

/**
 * 模块1函数5: 错误处理与报告
 */
void handle_error(int error_code, const char* error_description, const char* error_details) {
    // TC103 STEP2 log_error
    log_message(LOG_ERROR, "操作失败: %s (错误码: %d)", error_description, error_code);  // 通过桩插入
    if (error_details != NULL) {  // 通过桩插入
        log_message(LOG_DEBUG, "错误详情: %s", error_details);  // 通过桩插入
    }  // 通过桩插入
    
    // TC103 STEP2 segment2
    if (error_code >= CRITICAL_ERROR_THRESHOLD) {  // 通过桩插入
        send_admin_notification("系统错误", error_description);  // 通过桩插入
        log_message(LOG_INFO, "已发送管理员通知");  // 通过桩插入
    }  // 通过桩插入
    
    // TC103 STEP2 completed
    log_message(LOG_INFO, "错误处理流程已完成");  // 通过桩插入
    return ERROR_HANDLED;  // 通过桩插入
    
    printf("处理错误: %d, %s\n", error_code, error_description);
}
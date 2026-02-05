/* 验证函数 */

/**
 * 验证非空
 */
export function required(value: any): boolean {
  return value !== null && value !== undefined && value !== '';
}

/**
 * 验证字符串长度
 */
export function validateLength(value: string, min: number, max: number): boolean {
  return value.length >= min && value.length <= max;
}

/**
 * 验证数字范围
 */
export function validateRange(value: number, min: number, max: number): boolean {
  return value >= min && value <= max;
}

/**
 * 验证邮箱格式
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 验证文件名
 */
export function validateFilename(filename: string): boolean {
  // 不允许的字符
  const invalidChars = /[<>:"/\\|?*\x00-\x1F]/;
  // 保留的文件名
  const reservedNames = [
    'CON',
    'PRN',
    'AUX',
    'NUL',
    'COM1',
    'COM2',
    'COM3',
    'COM4',
    'COM5',
    'COM6',
    'COM7',
    'COM8',
    'COM9',
    'LPT1',
    'LPT2',
    'LPT3',
    'LPT4',
    'LPT5',
    'LPT6',
    'LPT7',
    'LPT8',
    'LPT9',
  ];

  if (invalidChars.test(filename)) {
    return false;
  }

  const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
  if (reservedNames.includes(nameWithoutExt.toUpperCase())) {
    return false;
  }

  return true;
}

/**
 * 验证PPT文件
 */
export function validatePPTFile(file: File): { valid: boolean; error?: string } {
  // 检查文件类型
  const allowedTypes = [
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.ms-powerpoint',
  ];
  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: '文件类型不正确，仅支持 .pptx 或 .ppt 文件' };
  }

  // 检查文件扩展名
  const validExtensions = ['.pptx', '.ppt'];
  const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
  if (!validExtensions.includes(extension)) {
    return { valid: false, error: '文件扩展名不正确，仅支持 .pptx 或 .ppt 文件' };
  }

  // 检查文件大小
  const maxSize = 100 * 1024 * 1024; // 100MB
  if (file.size > maxSize) {
    return { valid: false, error: '文件大小超过限制，最大支持 100MB' };
  }

  // 检查文件名
  if (!validateFilename(file.name)) {
    return { valid: false, error: '文件名包含非法字符' };
  }

  return { valid: true };
}

/**
 * 验证章节标题
 */
export function validateChapterTitle(title: string): { valid: boolean; error?: string } {
  if (!required(title)) {
    return { valid: false, error: '章节标题不能为空' };
  }

  if (!validateLength(title, 1, 100)) {
    return { valid: false, error: '章节标题长度应在1-100个字符之间' };
  }

  return { valid: true };
}

/**
 * 验证章节描述
 */
export function validateChapterDescription(description: string): { valid: boolean; error?: string } {
  if (!required(description)) {
    return { valid: false, error: '章节描述不能为空' };
  }

  if (!validateLength(description, 10, 500)) {
    return { valid: false, error: '章节描述长度应在10-500个字符之间' };
  }

  return { valid: true };
}

/**
 * 验证页数需求
 */
export function validateRequiredPages(pages: number): { valid: boolean; error?: string } {
  if (!validateRange(pages, 3, 8)) {
    return { valid: false, error: '每章节页数应在3-8页之间' };
  }

  return { valid: true };
}

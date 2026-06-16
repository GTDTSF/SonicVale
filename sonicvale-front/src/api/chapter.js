import request from './config'
import dayjs from 'dayjs'

export function getChaptersByProject(projectId) {
  return request.get(`/chapters/project/${projectId}`)
}

export function getChapterDetail(chapterId) {
  return request.get(`/chapters/${chapterId}`)
}


export function createChapter(title, projectId) {
  return request.post('/chapters', {
    title,
    project_id: projectId
  })
}


export function updateChapter(id, payload) {
  return request.put(`/chapters/${id}`, payload)
}

export function deleteChapter(chapterId) {
  return request.delete(`/chapters/${chapterId}`)
}


export function splitChapterByLLM(projectId, chapterId, sectionId = null) {
  const url = sectionId
    ? `/chapters/get-lines/${projectId}/${chapterId}?section_id=${sectionId}`
    : `/chapters/get-lines/${projectId}/${chapterId}`
  return request.get(url)
}





// 导出 LLM Prompt
export function exportLLMPrompt(projectId, chapterId) {
  // GET /export-llm-prompt/{project_id}/{chapter_id}
  return request.get(`/chapters/export-llm-prompt/${projectId}/${chapterId}`)
}

// 导入第三方 JSON（multipart/form-data，字段名 data）
export function importThirdLines(projectId, chapterId, formData) {
  // POST /import-lines/{project_id}/{chapter_id}
  // 注意：formData 已经是 FormData；不要再手动设置 boundary
  return request.post(`/chapters/import-lines/${projectId}/${chapterId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 智能匹配音色
// @router.post("/add-smart-role-and-voice/{project_id}/{chapter_id}",response_model=Res[str],summary="添加智能匹配角色和音色的功能",description="添加智能匹配角色和音色的功能")
// async def add_smart_role_and_voice(project_id: int,chapter_id: int,
// 自动分段
export function autoSplitChapter(chapterId) {
  return request.post(`/chapters/${chapterId}/auto-split`)
}

// 调整章节顺序
export function reorderChapter(chapterId, direction) {
  return request.put('/chapters/reorder', { project_id: chapterId, direction })
}

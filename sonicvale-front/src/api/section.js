import request from './config'

export function createSection(data) {
  return request.post('/sections', data)
}

export function getSectionsByChapter(chapterId) {
  return request.get(`/sections/chapter/${chapterId}`)
}

export function renameSection(sectionId, title) {
  return request.put(`/sections/${sectionId}`, { title })
}

export function deleteSection(sectionId) {
  return request.delete(`/sections/${sectionId}`)
}

export function getSectionDetail(sectionId) {
  return request.get(`/sections/${sectionId}`)
}

export function updateSectionContent(sectionId, data) {
  return request.put(`/sections/${sectionId}/content`, data)
}

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="glass-panel w-full max-w-2xl p-8 mx-4 animate-fade-in-up">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-white">导入人员名单</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-white transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- 文件上传区域 -->
      <div 
        @dragover.prevent="dragover = true"
        @dragleave.prevent="dragover = false"
        @drop.prevent="handleDrop"
        :class="[
          'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 mb-6',
          dragover 
            ? 'border-yellow-400 bg-yellow-400/10' 
            : 'border-white/20 hover:border-yellow-400 hover:bg-yellow-400/5'
        ]"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx,.xls,.csv"
          @change="handleFileSelect"
          class="hidden"
        />
        
        <svg class="w-16 h-16 mx-auto mb-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        
        <p class="text-xl font-bold text-white mb-2">点击上传 Excel 文件</p>
        <p class="text-gray-400">或拖拽文件到此处</p>
        <p class="text-sm text-gray-500 mt-4">支持 .xlsx、.xls 和 .csv 格式</p>
      </div>

      <!-- 文件信息展示 -->
      <div v-if="fileInfo" class="glass-panel p-6 mb-6 animate-fade-in-up">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <svg class="w-8 h-8 text-green-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p class="font-bold text-white">{{ fileInfo.name }}</p>
              <p class="text-sm text-gray-400">{{ (fileInfo.size / 1024).toFixed(2) }} KB</p>
            </div>
          </div>
          <button 
            @click="removeFile"
            class="text-red-400 hover:text-red-300 transition-colors"
          >
            移除
          </button>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div class="glass-panel p-4">
            <p class="text-sm text-gray-400 mb-1">总人数</p>
            <p class="text-3xl font-bold text-white">{{ importedData.length }}</p>
          </div>
          <div class="glass-panel p-4">
            <p class="text-sm text-gray-400 mb-1">示例数据</p>
            <p class="text-white truncate" v-if="importedData[0]">
              {{ importedData[0].name }} ({{ importedData[0].employeeId || '无工号' }})
            </p>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-4">
        <button
          @click="$emit('close')"
          class="px-6 py-3 rounded-lg border border-white/20 text-white hover:bg-white/10 transition-colors"
        >
          取消
        </button>
        <button
          @click="importData"
          :disabled="!importedData.length"
          :class="[
            'px-6 py-3 rounded-lg transition-colors font-bold',
            importedData.length 
              ? 'bg-gradient-to-r from-green-500 to-green-600 text-white hover:opacity-90 shadow-[0_0_20px_rgba(34,197,94,0.5)]' 
              : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          ]"
        >
          确定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import * as XLSX from 'xlsx'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close', 'import'])

const dragover = ref(false)
const fileInput = ref(null)
const selectedFile = ref(null)
const fileInfo = ref(null)
const importedData = ref([])
const availableColumns = ref([])
const mapping = ref({
  name: '姓名',
  employeeId: '工号'
})

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    processFile(file)
  }
}

// 处理拖放
const handleDrop = (event) => {
  dragover.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    processFile(file)
  }
}

// 处理文件
const processFile = (file) => {
  console.log('【ImportModal】开始处理文件:', file.name, file.type, file.size)
  
  // 检查文件类型
  const allowedTypes = [
    'application/vnd.ms-excel', 
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
    'text/csv',
    'application/vnd.ms-excel.sheet.macroEnabled.12'
  ]
  
  const allowedExtensions = /\.(xlsx|xls|csv)$/i
  
  if (!allowedTypes.includes(file.type) && !file.name.match(allowedExtensions)) {
    alert('请上传Excel或CSV文件（.xlsx, .xls, .csv）')
    console.error('【ImportModal】不支持的文件类型:', file.type)
    return
  }
  
  selectedFile.value = file
  fileInfo.value = {
    name: file.name,
    size: file.size,
    type: file.type
  }
  
  console.log('【ImportModal】文件信息已设置:', fileInfo.value)
  
  const reader = new FileReader()
  
  reader.onerror = (error) => {
    console.error('【ImportModal】文件读取错误:', error)
    alert('文件读取失败，请重试')
  }
  
  reader.onload = (e) => {
    try {
      console.log('【ImportModal】文件读取成功，开始解析')
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      console.log('【ImportModal】工作簿sheet数量:', workbook.SheetNames.length)
      
      if (workbook.SheetNames.length === 0) {
        throw new Error('Excel文件没有工作表')
      }
      
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })
      
      console.log('【ImportModal】解析后的原始数据行数:', jsonData.length)
      console.log('【ImportModal】前3行数据:', jsonData.slice(0, 3))
      
      // 获取表头（第一行）
      const headers = jsonData[0] || []
      availableColumns.value = headers.filter(h => h && h.trim())
      
      console.log('【ImportModal】检测到的列:', availableColumns.value)
      
      // 自动匹配字段
      autoMatchFields(headers)
      console.log('【ImportModal】字段映射:', mapping.value)
      
      // 解析数据行（从第二行开始）
      parseData(jsonData.slice(1), headers)
      console.log('【ImportModal】解析完成，导入数据数量:', importedData.value.length)
    } catch (error) {
      console.error('【ImportModal】解析Excel文件失败:', error)
      console.error('【ImportModal】错误堆栈:', error.stack)
      alert(`解析文件失败: ${error.message || '请检查文件格式'}`)
      removeFile()
    }
  }
  
  reader.readAsArrayBuffer(file)
}

// 自动匹配字段
const autoMatchFields = (headers) => {
  const namePatterns = ['姓名', '名字', '员工姓名', 'name', 'Name', '姓名/Name']
  const idPatterns = ['工号', '员工编号', '员工号', '编号', 'id', 'ID', '员工ID']
  
  const nameCol = headers.find(header => 
    namePatterns.some(pattern => 
      header.toString().toLowerCase().includes(pattern.toLowerCase())
    )
  )
  
  const idCol = headers.find(header => 
    idPatterns.some(pattern => 
      header.toString().toLowerCase().includes(pattern.toLowerCase())
    )
  )
  
  if (nameCol) {
    mapping.value.name = nameCol
  } else if (availableColumns.value.length > 0) {
    mapping.value.name = availableColumns.value[0]
  }
  
  if (idCol) {
    mapping.value.employeeId = idCol
  }
}

// 解析数据
const parseData = (rows, headers) => {
  importedData.value = []
  
  rows.forEach((row, index) => {
    // 跳过空行
    if (!row || row.every(cell => !cell && cell !== 0)) return
    
    const rowData = {}
    headers.forEach((header, colIndex) => {
      if (header && header.trim()) {
        rowData[header] = row[colIndex]
      }
    })
    
    // 根据映射创建用户对象
    const user = {
      name: String(rowData[mapping.value.name] || `员工${index + 1}`).trim(),
      employeeId: mapping.value.employeeId ? String(rowData[mapping.value.employeeId] || '').trim() : '',
      isFake: false
    }
    
    if (user.name) {
      importedData.value.push(user)
    }
  })
  
  console.log(`成功解析 ${importedData.value.length} 条数据`)
}

// 移除文件
const removeFile = () => {
  selectedFile.value = null
  fileInfo.value = null
  importedData.value = []
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 导入数据
const importData = () => {
  console.log('【ImportModal】========== 开始导入流程 ==========')
  console.log('【ImportModal】导入数据按钮被点击')
  console.log('【ImportModal】当前导入数据数量:', importedData.value.length)
  console.log('【ImportModal】原始导入数据:', importedData.value)
  
  if (importedData.value.length === 0) {
    console.warn('【ImportModal】没有可导入的数据')
    alert('请先上传有效的人员名单')
    return
  }
  
  // 确保数据格式正确，并添加必要的字段
  const formattedData = importedData.value.map((user, index) => {
    const formatted = {
      name: String(user.name || '').trim(),
      employeeId: String(user.employeeId || '').trim(),
      id: user.employeeId || `imported_${Date.now()}_${index}`,  // 添加 id
      userId: user.employeeId || `imported_${Date.now()}_${index}`, // 添加 userId
      isFake: false
    }
    
    // 验证必填字段
    if (!formatted.name) {
      console.warn('【ImportModal】跳过无效用户（无姓名）:', user)
      return null
    }
    
    return formatted
  }).filter(user => user !== null) // 过滤掉无效数据
  
  console.log('【ImportModal】格式化后数据数量:', formattedData.length)
  console.log('【ImportModal】格式化后示例数据:', formattedData.slice(0, 3))
  
  if (formattedData.length === 0) {
    console.error('【ImportModal】格式化后没有有效数据')
    alert('导入失败：没有有效的用户数据（至少需要姓名）')
    return
  }
  
  // 触发导入事件
  console.log('【ImportModal】准备触发 import 事件，数据:', formattedData)
  try {
    emit('import', formattedData)
    console.log('【ImportModal】已成功触发 import 事件')
  } catch (error) {
    console.error('【ImportModal】触发 import 事件失败:', error)
    alert(`导入失败: ${error.message || '未知错误'}`)
    return
  }
  
  // 关闭模态框
  console.log('【ImportModal】准备关闭模态框')
  emit('close')
  console.log('【ImportModal】已触发 close 事件')
  
  // 重置状态
  removeFile()
  console.log('【ImportModal】========== 导入流程完成 ==========')
}

// 监听显示状态，重置时清空
watch(() => props.show, (newVal) => {
  if (!newVal) {
    removeFile()
  }
})
</script>

<style scoped>
.glass-panel {
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.7);
}

.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>


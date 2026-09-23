<template>
  <el-card shadow="never">
    <template #header>
      <div class="report-header">
        <span>智能数据报表</span>
        <el-tag size="small" type="info">阶段七实现 · 当前展示 ECharts 集成示例</el-tag>
      </div>
    </template>
    <div ref="chartRef" class="report-chart"></div>
  </el-card>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let chart = null

function renderChart() {
  chart = echarts.init(chartRef.value)
  chart.setOption({
    title: { text: '示例图表（ECharts 已接入）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    grid: { left: 40, right: 20, top: 40, bottom: 50 },
    xAxis: { type: 'category', data: ['一月', '二月', '三月', '四月', '五月', '六月'] },
    yAxis: { type: 'value' },
    series: [
      { name: '销售额', type: 'bar', data: [120, 200, 150, 80, 70, 110], itemStyle: { color: '#409eff' } },
      { name: '订单量', type: 'line', data: [90, 130, 100, 70, 60, 90], itemStyle: { color: '#67c23a' } },
    ],
  })
}

function onResize() {
  chart && chart.resize()
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart && chart.dispose()
})
</script>

<style scoped>
.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.report-chart {
  width: 100%;
  height: 480px;
}
</style>
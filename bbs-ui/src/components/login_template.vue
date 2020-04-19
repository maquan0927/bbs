<template>
  <div>
    <el-row type="flex" justify="center" align="middle">
      <el-col :span="12" :style="{'height': clientHeight + 'px', 'background-color': '#f5f5f5'}">
        <el-col :span="8" style="height: 10px;"></el-col>
        <el-col :span="16" style="margin-top: 45%;">
          <i class="iconfont icon-luntanzixun"></i>
          <span>B.B.S</span>
          <span style="top: 60%;">校园论坛</span>
        </el-col>
      </el-col>

      <el-col :span="12">
        <router-view :key="$route.fullPath"></router-view>
        <el-row type="flex" justify="center" style="position: fixed;bottom: 10px;left: 68%;">
          <div>马泉 ©2020 </div>
        </el-row>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  data() {
    return {
      clientHeight: null,
    }
  },
  mounted() {
    // 动态设置背景图的高度为浏览器可视区域高度
    // 首先在Virtual DOM渲染数据时，设置下背景图的高度．
    // 测试发现需延时50ms才能设置生效
    setTimeout(_=>{
      this.clientHeight = document.documentElement.clientHeight
    }, 50)
    // 然后监听window的resize事件．在浏览器窗口变化时再设置下背景图高度．
    window.onresize = function () {
      this.clientHeight = document.documentElement.clientHeight
    }
  },
}
</script>
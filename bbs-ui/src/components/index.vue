<template>
  <!-- 容器 -->
  <el-container>
    
    <!-- 顶部导航 -->
    <el-header>
      <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal" @select="handleSelect">
        <el-menu-item>
          <i class="iconfont icon-luntanzixun" style="font-size: 30px;"></i>
        </el-menu-item>
        <el-menu-item index="ui">首页</el-menu-item>
        <el-submenu index="2">
          <template slot="title">我的工作台</template>
          <el-menu-item index="2-1">选项1</el-menu-item>
          <el-menu-item index="2-2">选项2</el-menu-item>
          <el-menu-item index="2-3">选项3</el-menu-item>
          <el-submenu index="2-4">
            <template slot="title">选项4</template>
            <el-menu-item index="2-4-1">选项1</el-menu-item>
            <el-menu-item index="2-4-2">选项2</el-menu-item>
            <el-menu-item index="2-4-3">选项3</el-menu-item>
          </el-submenu>
        </el-submenu>
        <el-menu-item index="3">消息中心</el-menu-item>
        <el-submenu index="user_info">
          <template slot="title">
            <i class="el-icon-user-solid"></i>
          </template>
          <template v-if="$cookie.get('access_token')">
            <el-menu-item index="logout">退出登陆</el-menu-item>
          </template>
          <template v-else>
            <el-menu-item index="login">登陆</el-menu-item>
          </template>
        </el-submenu>
      </el-menu>
    </el-header>

    <!-- 主要区域 -->
    <el-main :style="{ height: clientHeight - 60 + 'px'}">
      <div style="overflow: scroll; background:#fff; padding: 15px 20px;" :style="{ height: clientHeight - 130 + 'px'}">
        <router-view :key="$route.fullPath"></router-view>
      </div>
    </el-main>

  </el-container>
</template>

<script>
export default {
  data() {
    return {
      activeIndex: 'ui',
      route_maps: {
        "index": "/ui",
        "ui": "/ui",
        "login": "/ui/login"
      },
    }
  },
  created(){
    console.log(this.user_info)
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
  methods: {
    handleSelect(key, keyPath) {
      if (key === 'logout'){
        this.logout()
      }
      if (key in this.route_maps) {
        this.$router.push(this.route_maps[key])
      }
    },
    logout() {
      this.$cookie.delete('access_token');
      this.$cookie.delete('refresh_token');
      this.$cookie.delete('username')
      this.$router.push('/ui/login')
    }
  },
  computed: {
    clientHeight: {
      get(){
        return this.$store.state.clientHeight
      },
      set(value){
        this.$store.commit('set_client_height', value)
      }
    },
    user_info: {
      get(){
        return this.$store.state.user_info
      },
      set(value){
        this.$store.commit('set_user_info', value)
      }
    }
  }
}
</script>

<style scoped>
  .el-main {
    background-color: #f9f9f9;
    color: #333;
  }
</style>
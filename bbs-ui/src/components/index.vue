<template>
  <!-- 容器 -->
  <el-container>
    
    <!-- 顶部导航 -->
    <el-header>
      <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal" @select="handleSelect">
        <el-menu-item index="index">
          <i class="iconfont icon-luntanzixun" style="font-size: 30px;"></i>
        </el-menu-item>
        <el-menu-item index="ui">首页</el-menu-item>
        <el-menu-item v-for="(modu,index) in module" :key="index" :index="modu.name">{{ modu.name }}</el-menu-item>
        <el-submenu index="module_admin" v-if="user_info.is_superuser">
          <template slot="title">
            板块管理
          </template>
          <el-menu-item index="module_add">新增板块</el-menu-item>
          <el-menu-item index="module_update">修改板块</el-menu-item>
          <el-menu-item index="module_del">删除板块</el-menu-item>
        </el-submenu>
        <el-submenu index="user_info">
          <template slot="title">
            <i class="el-icon-user-solid"></i>
          </template>
          <template v-if="$cookie.get('access_token')">
            <el-menu-item index="user">个人信息</el-menu-item>
            <el-menu-item index="logout">退出登陆</el-menu-item>
          </template>
          <template v-else>
            <el-menu-item index="login">登陆</el-menu-item>
            <el-menu-item index="register">注册</el-menu-item>
          </template>
        </el-submenu>
      </el-menu>
    </el-header>

    <!-- 主要区域 -->
    <el-main :style="{ height: (clientHeight - 60) + 'px'}">
      <div style="overflow: scroll; background:#fff; padding: 15px 20px;" :style="{ height: (clientHeight - 130) + 'px'}">
        <router-view :key="$route.fullPath"></router-view>
      </div>
    </el-main>

    <el-dialog title="板块管理" :visible.sync="module_admin_dialog">
      <el-form :model="module_form" :rules="module_form_rules" ref="module_form" label-width="100px">
        <el-form-item label="管理板块" prop="module" v-if="['module_update', 'module_del'].includes(module_admin_type)">
          <el-select v-model="module_form.module" filterable placeholder="请选择板块模块" style="width: 80%;" @change="module_change">
            <el-option v-for="(module, index) in module" :key="index" :label="module.name" :value="module.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="板块名称" prop="name" v-if="['module_update', 'module_add'].includes(module_admin_type)">
          <el-input v-model="module_form.name" style="width: 80%;" placeholder="请输入板块名字"></el-input>
        </el-form-item>
        <el-form-item label="板块管理员" prop="admin" v-if="['module_update', 'module_add'].includes(module_admin_type)">
          <el-select v-model="module_form.admin" multiple filterable placeholder="请选择板块管理员" style="width: 80%;">
            <el-option v-for="(user, index) in all_user_options" :key="index" :label="user.username" :value="user.id"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancel_module">取 消</el-button>
        <el-button type="primary" @click="submit_module">确 定</el-button>
      </div>
    </el-dialog>

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
        "login": "/ui/login",
        "register": "/ui/register",
        "user": '/ui/user'
      },
      module_admin_dialog: false,
      module_admin_type: null,
      all_user_options: [],
      module_form: {
        module: null,
        name: null,
        admin: []
      },
      module_form_rules: {
        module: [
          { required: true, message: '请选择管理的板块', trigger: 'change' },
        ],
        admin: [
          { type: 'array', required: true, message: '请选择管理员', trigger: 'change' },
        ],
        name: [
          { required: true, message: '请输入板块名', trigger: 'blur' },

        ],
      }
    }
  },
  created(){
    this.load_module()
    this.load_user()
    this.load_all_user()
  },
  mounted() {
    const $this = this;
    // 动态设置背景图的高度为浏览器可视区域高度
    // 首先在Virtual DOM渲染数据时，设置下背景图的高度．
    // 测试发现需延时50ms才能设置生效
    setTimeout(_=>{
      $this.clientHeight = document.documentElement.clientHeight
    }, 50)
    // 然后监听window的resize事件．在浏览器窗口变化时再设置下背景图高度．
    window.onresize = function () {
      $this.clientHeight = document.documentElement.clientHeight
    }
  },
  methods: {
    cancel_module() {
      this.module_form = {
        module: null,
        name: null,
        admin: []
      }
      this.module_admin_dialog = false
    },
    submit_module() {
      let url_dict = {
        module_add: '/api/module/',
        module_del: '/api/module/' + this.module_form.module + '/',
        module_update: '/api/module/' + this.module_form.module + '/',
      }
      let request_dict = {
        module_add: 'post',
        module_del: 'delete',
        module_update: 'patch'
      }
      this.$refs['module_form'].validate((valid) => {
        if (valid) {
          this.axios[request_dict[this.module_admin_type]](url_dict[this.module_admin_type], this.module_form)
          .then(res => {
            this.module_admin_dialog = false
            this.$alert('页面即将刷新', '成功', {
              confirmButtonText: '确定',
              callback: action => {
                this.$router.go(0)
              }
            });
          })
        }else{
          return false
        }
      });
    },
    module_change(val){
      for(let i of this.module){
        if(i.id == val){
          this.module_form.name = i.name
          this.module_form.admin = i.admin
        }
      }
    },
    load_all_user() {
      if(!this.$cookie.get('access_token')){
        return false
      }
      if(!this.user_info.is_superuser){
        return false
      }
      this.axios.get('/api/user/')
      .then(res => {
        this.all_user_options = res.data
      })
    },
    load_user() {
      if(!this.$cookie.get('access_token')){
        return
      }
      this.axios.get('/api/user/detail/')
      .then(res => {
        this.user_info = res.data
      })
    },
    load_module(){
      const $this = this
      this.axios.get('/api/module/')
      .then(res => {
        for(let i of res.data){
          this.route_maps[i.name] = '/ui/module/' + i.id
        }
        this.module = res.data
      })
    },
    handleSelect(key, keyPath) {
      if (key === 'logout'){
        this.logout()
      }else if(['module_add', 'module_update', 'module_del'].includes(key)){
        this.module_admin_dialog = true
        this.module_admin_type = key
        return
      }
      if (key in this.route_maps) {
        this.$router.push(this.route_maps[key])
      }
    },
    logout() {
      this.$cookie.delete('access_token');
      this.$cookie.delete('refresh_token');
      this.$cookie.delete('username')
      this.$router.go(0)
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
    module: {
      get(){
        return this.$store.state.module
      },
      set(value){
        this.$store.commit('set_module', value)
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
  },
}
</script>

<style scoped>
  .el-main {
    background-color: #f9f9f9;
    color: #333;
  }
</style>
<template>
  <!-- 容器 -->
  <el-container>
    
    <!-- 顶部导航 -->
    <el-header>
      <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal" @select="handleSelect">
        <el-menu-item index="ui">首页</el-menu-item>
        <el-menu-item index="message">留言</el-menu-item>
        <el-menu-item index="logout" v-if="$cookie.get('access_token')">退出登陆</el-menu-item>
      </el-menu>
    </el-header>

    <!-- 主要区域 -->
    <el-main :style="{ height: clientHeight - 60 + 'px'}">
      <div style="overflow: scroll; background:#fff; padding: 15px 20px;" :style="{ height: clientHeight - 130 + 'px'}">
        <!-- 走马灯 -->
        <br>
          <h3>风景轮播</h3>
        <br>
        
        <el-row>
          <el-col :span="24">
            <el-carousel :interval="1000" type="card" height="300px">
              <el-carousel-item v-for="(item, index) in index_img" :key="index">
                <img :src="item.img" alt="" width="100%;">
              </el-carousel-item>
            </el-carousel>
          </el-col>
        </el-row>

        <h3>热门推荐</h3>
        <br>

        <el-row>
          <el-col :span="8" v-for="(item, index) in recomend_data" :key="index" style="text-align: center;">
            <img :src="item.img" alt="" width="98%" height="250px" @click="show_drawer('recomend', item)">
            <h4 @click="show_drawer('recomend', item)"><el-link type="primary">{{ item.title }}</el-link></h4>
          </el-col>
        </el-row>

        <br>
        <h3>导游风采</h3>
        <br>

        <el-row>
          <el-col :span="8" v-for="(item, index) in tourguide_data" :key="index" style="text-align: center;">
            <img :src="item.img" alt="" width="98%" height="250px" @click="show_drawer('tourguide', item)">
            <h4 @click="show_drawer('tourguide', item)"><el-link type="primary">{{ item.title }}</el-link></h4>
          </el-col>
        </el-row>
      </div>
    </el-main>

    <!-- 景点和导游使用的抽屉 -->
    <el-dialog
      :title="drawer_data.title"
      :visible.sync="drawer">
      <img :src="drawer_data.img" alt="" width="100%">
      <div style="width: 90%; margin: 20px auto;">{{ drawer_data.content }}</div>
    </el-dialog>

    <el-dialog
      width="50%"
      title="登陆"
      :visible.sync="login_dialog">
      <el-form :model="loginform" ref="loginform" :rules="login_rules">
        <el-form-item label="用户名" label-width="100px" prop="username">
          <el-input v-model="loginform.username" autocomplete="off" style="width: 70%;"></el-input>
        </el-form-item>
        <el-form-item label="密码" label-width="100px" prop="password">
          <el-input v-model="loginform.password" autocomplete="off" show-password style="width: 70%;"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" @click="show_register">注 册</el-button>
        <el-button @click="login_dialog = false">取 消</el-button>
        <el-button type="primary" @click="login">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog
      width="50%"
      title="留言"
      :visible.sync="register_dialog">
      <el-form :model="messageform" ref="messageform" :rules="message_rules">
        <el-form-item label="标题" label-width="100px" prop="title">
          <el-input v-model="messageform.title" autocomplete="off" style="width: 70%;"></el-input>
        </el-form-item>
        <el-form-item label="内容" label-width="100px" prop="content">
          <el-input type="textarea" :autosize="{ minRows: 5, maxRows: 10}" v-model="messageform.content" autocomplete="off" style="width: 70%;"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="message_dialog = false">取 消</el-button>
        <el-button type="primary" @click="submit_message">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog
      width="50%"
      title="注册"
      :visible.sync="register_dialog">
      <el-form :model="register_form" ref="register_form" :rules="login_rules">
        <el-form-item label="用户名" label-width="100px" prop="username">
          <el-input v-model="register_form.username" autocomplete="off" style="width: 70%;"></el-input>
        </el-form-item>
        <el-form-item label="密码" label-width="100px" prop="password">
          <el-input v-model="register_form.password" autocomplete="off" show-password style="width: 70%;"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="register_dialog = false">取 消</el-button>
        <el-button type="primary" @click="register">注 册</el-button>
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
        "ui": "/ui",
      }, 
      drawer: false,
      login_dialog: false,
      register_dialog: false,
      message_dialog: false,
      register_form: {
        username: null,
        password: null
      },
      loginform: {
        user: null,
        password: null,
      },
      messageform: {
        title: null,
        content: null
      },
      drawer_data: {},
      index_img: [],
      recomend_data: [],
      tourguide_data: [],
      login_rules: {
        username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
        password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
      },
      message_rules: {
        title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
        content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
      },
    }
  },
  created(){
    this.load_index_img()
    this.load_recommend()
    this.load_tourguide()
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
    register(){
      this.$refs["register_form"].validate((valid) => {
        if (valid) {
          this.axios.post('/api/user/', this.register_form)
          .then(res => {
            this.$message.success("注册成功")
            this.register_dialog = false
            this.login_dialog = true
          })
        }else{
          return false
        }
      })
    },
    show_register(){
      this.login_dialog = false
      this.register_dialog = true
    },
    submit_message(){
      this.$refs["messageform"].validate((valid) => {
        if (valid) {
          this.axios.post('/api/message/', this.messageform)
          .then(res => {
            this.$message.success("留言成功")
            this.message_dialog = false
          })
        }else{
          return false
        }
      })
    },
    logout() {
      this.$cookie.delete('access_token');
      this.$cookie.delete('refresh_token');
      this.$cookie.delete('username')
      this.$router.go(0)
    },
    login(){
      const $this = this
      this.$refs["loginform"].validate((valid) => {
        if (valid) {
          let params = new URLSearchParams();
          params.append('grant_type', 'password');
          params.append('username', this.loginform.username);
          params.append('password', this.loginform.password);
          params.append('client_id', 'l5cLs3BFLXQCQo1Jkm0hFTo66iJGkkQRxgGmuvDu');
          params.append('client_secret', 'TnqjcKs3RZ5Rlh9Dz3csYSy7dk1Yk0YRhN7qgIF04TP9mc1Av5KfRdCtxps1c1s6314sWht5Rg1ojym3ZY4GR4J8zWqIBfwMIvS1n700PtFOIEwZDELVxbpVTmTgxi2x');
          this.axios.post('/oauth/token/', params, {
            headers: {"Content-Type": "application/x-www-form-urlencoded"},
            timeout: 10000
          }).then((res)=>{
            if(res.status === 200) {
              $this.$message.success("登陆成功")
              let expires = res.data['expires_in'] + 's'
              $this.$cookie.set('access_token', res.data['access_token'], {expires});
              $this.$cookie.set('refresh_token', res.data['refresh_token'], {expires});
              $this.$cookie.set('token_type', res.data['token_type'], {expires});
              this.login_dialog = false
              this.message_dialog = true
            }else{
              $this.$message({message: "登录失败！请检查您的用户名密码", type: 'error'});
            }
          }).catch((error)=>{
            console.log(error)
            $this.$message({message: "登录失败！请检查您的用户名密码", type: 'error'});
            $this.$cookie.delete('access_token');
            $this.$cookie.delete('refresh_token');
            $this.$cookie.delete('username')
          });
        } else {
          return false;
        }
      });
    },
    handleSelect(key, keyPath) {
      if (key === 'message'){
        if(!this.check_login()){
          this.login_dialog = true
        }else{
          this.message_dialog = true
        }
      }else if(key === 'logout'){
        this.logout()
      }
    },
    show_drawer(type, data){
      this.drawer = true
      this.drawer_data = data
    },
    load_index_img(){
      this.axios.get('/api/index/')
      .then(res => {
        this.index_img = res.data
      })
    },
    load_recommend(){
      this.axios.get('/api/recomend/')
      .then(res => {
        this.recomend_data = res.data
      })
    },
    load_tourguide(){
      this.axios.get('/api/tourguide/')
      .then(res => {
        this.tourguide_data = res.data
      })
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
  },
}
</script>

<style scoped>
  .el-main {
    background-color: #f9f9f9;
    color: #333;
  }
</style>
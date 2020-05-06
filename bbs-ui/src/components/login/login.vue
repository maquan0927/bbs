<template>
  <div>
    <el-form :model="login_form" status-icon :rules="rules" ref="login_form" label-width="100px">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="login_form.username" style="width: 70%;"></el-input>
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input type="password" v-model="login_form.password" style="width: 70%;" show-password></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="login">登陆</el-button>
        <el-button type="primary" @click="go_to_register">注册</el-button>
      </el-form-item>
    </el-form>   
  </div>
</template>

<script>
export default {
  data() {
    return {
      login_form: {
        username: null,
        password: null,
      },
      loading: false,
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
        ],
      }
    }
  },
  methods: {
    login() {
      let $this = this
      this.$refs["login_form"].validate((valid) => {
        if (valid) {
          let params = new URLSearchParams();
          params.append('grant_type', 'password');
          params.append('username', this.login_form.username);
          params.append('password', this.login_form.password);
          params.append('client_id', '556H3wPz6VjDNuHPapCBVc3CsR3cfvhLgcElb88M');
          params.append('client_secret', '0LkwAp1U84IB3fkY6finw4EfyFdTu311ALdfZHploSEnKprUlG8uxWOKhv0xhEEmDXCOa4vljUI1syLT3qGoIfwws0lkt26QltsBGumjc5Fl1inWQGpg72AavQ7mExaj');
          this.loading = true
          this.axios.post('/oauth/token/', params, {
            headers: {"Content-Type": "application/x-www-form-urlencoded"},
            timeout: 10000
          }).then((res)=>{
            $this.loading = false
            if(res.status === 200) {
              let expires = res.data['expires_in'] + 's'
              $this.$cookie.set('access_token', res.data['access_token'], {expires});
              $this.$cookie.set('refresh_token', res.data['refresh_token'], {expires});
              $this.$cookie.set('token_type', res.data['token_type'], {expires});
              this.axios.get('/api/user/detail/')
              .then(res => {
                this.user_info = res.data
              })
              // 跳转到之前需要进入的页面
              let next = $this.$route.query.next
              if(next){
                $this.$router.push(next)
              }else{
                $this.$router.push('/ui')
              }
            }else{
              $this.$message({message: "登录失败！请检查您的用户名密码", type: 'error'});
            }
          }).catch((error)=>{
            $this.loading = false
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
    go_to_register() {
      this.$router.push('/ui/register')
    },
  },
  computed: {
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
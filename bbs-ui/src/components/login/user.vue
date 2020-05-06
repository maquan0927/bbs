<template>
  <div>
    <el-form :model="form" :rules="rules" ref="form" label-width="100px">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="用户名" style="width: 70%;" disabled></el-input>
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" placeholder="密码,如不需要修改密码请不要输入密码" style="width: 70%;" show-password></el-input>
      </el-form-item>

      <el-form-item label="确认密码" prop="check_password">
        <el-input v-model="form.check_password" placeholder="确认密码,如不需要修改密码请不要输入密码" style="width: 70%;" show-password></el-input>
      </el-form-item>

      <el-form-item label="出生日期" prop="birthday">
        <el-date-picker v-model="form.birthday" value-format="yyyy-MM-dd" format="yyyy 年 MM 月 dd 日" type="date" placeholder="生日" style="width: 70%;"></el-date-picker>
      </el-form-item>

      <el-form-item label="性别" prop="sex">
        <el-radio-group v-model="form.sex">
          <el-radio-button :label="1">男</el-radio-button>
          <el-radio-button :label="0">女</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="update_user">修改信息</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        username: null,
        password: null,
        check_password: null,
        email: null,
        birthday: null,
        sex: 1,
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
        ],
        password: [
          { min: 8, max: 16, message: '长度在8到16个字符', trigger: 'blur' }
        ],
        check_password: [
          { validator: (rule, value, callback) => {
              if(value != this.form.password){
                callback(new Error('两次密码输入不一致'))
              }
              callback()
            },
            trigger: 'blur'
          },
        ],
        birthday: [
          { required: true, message: '请选择出生日期', trigger: 'change' },
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' }
        ],
      }
    }
  },
  methods: {
    update_user() {
      this.axios.patch('/api/user/detail/', this.form)
      .then(res => {
        if(res.status == 200){
          this.$message.success('信息修改成功');
          this.$router.push('/ui')
        }
      })
    }
  },
  created() {
    console.log(this.$cookie.get('access_token'))
    if(!this.$cookie.get('access_token')){
      this.$router.push('/ui')
    }
    this.axios.get('/api/user/detail/')
    .then(res => {
      this.form = res.data
    })
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
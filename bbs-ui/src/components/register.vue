<template>
  <div>
    <el-form :model="form" :rules="rules" ref="form" label-width="100px">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="用户名" style="width: 70%;"></el-input>
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" placeholder="密码" style="width: 70%;" show-password></el-input>
      </el-form-item>

      <el-form-item label="确认密码" prop="check_password">
        <el-input v-model="form.check_password" placeholder="确认密码" style="width: 70%;" show-password></el-input>
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="邮箱" style="width: 70%;"></el-input>
        <el-button type="primary" style="width: 20%;" :disabled="is_send_code" @click="send_code">{{ is_send_code ? code_time : '发送验证码' }}</el-button>
      </el-form-item>

      <el-form-item label="验证码" prop="code">
        <el-input v-model="form.code" placeholder="验证码" style="width: 70%;"></el-input>
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
        <el-button type="primary" @click="create_user">注册用户</el-button>
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
      is_send_code: false,
      code_time: 300,
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 8, max: 16, message: '长度在8到16个字符', trigger: 'blur' }
        ],
        check_password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
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
        code: [
          { required: true, message: '请输入验证码', trigger: 'blur' }
        ]
      }
    }
  },
  methods: {
    send_code() {
      if(!this.form.email){
        this.$alert('请输入邮箱', '邮箱', {
          confirmButtonText: '确定',
          showClose: false,
          callback: action => {
          }
        });
      }else{
        this.axios.post('/api/user/email/', {email: this.form.email})
        .then(res => {
          this.$message({
            type: 'success',
            message: '验证码发送成功, 三分钟内有效'
          });
          this.is_send_code = true
          this.code_time = 300
          this.send_code_timer = setInterval(_ => {
            if(this.code_time == 0){
              this.is_send_code = false
              clearInterval(this.send_code_timer)
            }
            this.code_time -= 1
          }, 1000)
        })
      }
    },
    create_user() {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          this.axios.post('/api/user/', this.form)
          .then(res => {
            if(res.status == 201){
              this.$alert('请登陆或者继续浏览', '注册成功', {
                confirmButtonText: '确定',
                callback: action => {
                  this.$router.push('/ui')
                }
              })
            }else if(res.status == 302){
              this.$message.error('验证码错误，请重新输入或者重新发送验证码');
            }else{
              this.$message.error('用户名或邮箱已存在，请重新输入');
            }
          })
        } else {
          console.log('error submit!!');
          return false;
        }
      });
    }
  },
}
</script>
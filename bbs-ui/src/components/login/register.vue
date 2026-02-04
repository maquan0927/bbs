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
        <el-input v-model="form.email" placeholder="邮箱" style="width: 50%;"></el-input>
        <el-button type="primary" style="width: 20%;" :disabled="isSendCode" @click="sendCode">{{ isSendCode ? codeTime : '发送验证码' }}</el-button>
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
        <el-button type="primary" @click="createUser">注册</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
// 配置常量
const CODE_COUNTDOWN = 300 // 验证码倒计时秒数
const password_MIN_LENGTH = 8
const password_MAX_LENGTH = 16

export default {
  name: 'Register',
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
      isSendCode: false,
      codeTime: CODE_COUNTDOWN,
      sendCodeTimer: null,
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: password_MIN_LENGTH, max: password_MAX_LENGTH, message: `长度在${password_MIN_LENGTH}到${password_MAX_LENGTH}个字符`, trigger: 'blur' }
        ],
        check_password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              if (value !== this.form.password) {
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
  beforeDestroy() {
    // 清理定时器，防止内存泄漏
    this.clearCodeTimer()
  },
  methods: {
    /**
     * 清理验证码倒计时定时器
     */
    clearCodeTimer() {
      if (this.sendCodeTimer) {
        clearInterval(this.sendCodeTimer)
        this.sendCodeTimer = null
      }
    },

    /**
     * 发送验证码
     */
    sendCode() {
      if (!this.form.email) {
        this.$alert('请输入邮箱', '邮箱', {
          confirmButtonText: '确定',
          showClose: false,
        })
        return
      }

      this.axios.post('/api/user/email/', { email: this.form.email })
        .then(res => {
          this.$message({
            type: 'success',
            message: '验证码发送成功, 三分钟内有效'
          })
          this.isSendCode = true
          this.codeTime = CODE_COUNTDOWN

          // 清理旧的定时器
          this.clearCodeTimer()

          // 启动新的倒计时
          this.sendCodeTimer = setInterval(() => {
            if (this.codeTime <= 0) {
              this.isSendCode = false
              this.clearCodeTimer()
              return
            }
            this.codeTime -= 1
          }, 1000)
        })
        .catch(err => {
          this.$message.error('发送验证码失败，请稍后重试')
          console.error('发送验证码失败:', err)
        })
    },

    /**
     * 创建用户
     */
    createUser() {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          this.axios.post('/api/user/', this.form)
            .then(res => {
              if (res.status === 201) {
                this.$alert('请登陆或者继续浏览', '注册成功', {
                  confirmButtonText: '确定',
                  callback: () => {
                    this.$router.push('/ui')
                  }
                })
              } else if (res.status === 302) {
                this.$message.error('验证码错误，请重新输入或者重新发送验证码')
              } else {
                this.$message.error('用户名或邮箱已存在，请重新输入')
              }
            })
            .catch(err => {
              this.$message.error('注册失败，请稍后重试')
              console.error('注册失败:', err)
            })
        }
      })
    }
  },
}
</script>

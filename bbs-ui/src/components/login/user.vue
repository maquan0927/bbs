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
        <el-button type="primary" @click="updateUser">修改信息</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
// 配置常量
const password_MIN_LENGTH = 8
const password_MAX_LENGTH = 16

export default {
  name: 'User',
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
          { min: password_MIN_LENGTH, max: password_MAX_LENGTH, message: `长度在${password_MIN_LENGTH}到${password_MAX_LENGTH}个字符`, trigger: 'blur' }
        ],
        check_password: [
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
      }
    }
  },
  created() {
    // 检查登录状态
    if (!this.$cookie.get('access_token')) {
      this.$router.push('/ui')
      return
    }
    this.loadUserInfo()
  },
  methods: {
    /**
     * 加载用户信息
     */
    loadUserInfo() {
      this.axios.get('/api/user/detail/')
        .then(res => {
          this.form = res.data
        })
        .catch(err => {
          this.$message.error('加载用户信息失败')
          console.error('加载用户信息失败:', err)
        })
    },

    /**
     * 更新用户信息
     */
    updateUser() {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          this.axios.patch('/api/user/detail/', this.form)
            .then(res => {
              if (res.status === 200) {
                this.$message.success('信息修改成功')
                this.$router.push('/ui')
              }
            })
            .catch(err => {
              this.$message.error('修改失败，请稍后重试')
              console.error('修改用户信息失败:', err)
            })
        }
      })
    }
  }
}
</script>

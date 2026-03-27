<template>
  <el-container class="layout-container">
    <el-aside width="200px" style="background-color: #304156;">
      <div class="logo-title">
        <h3 style="color: white; text-align: center; margin: 20px 0;">违停检测后台</h3>
      </div>
      <el-menu
        active-text-color="#409eff"
        background-color="#304156"
        text-color="#bfcbd9"
        :default-active="$route.path"
        router
      >
        <el-menu-item index="/audit">
          <el-icon><View /></el-icon>
          <span>违规复核台</span>
        </el-menu-item>
        <el-menu-item index="/report">
          <el-icon><Document /></el-icon>
          <span>报告展示看板</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="text-align: right; font-size: 12px; border-bottom: 1px solid #ccc; line-height: 60px;">
        <span style="font-size: 16px; font-weight: bold; margin-right: auto; float: left;">校园违规停车报告生成系统</span>
        <span>Admin</span>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style>
body {
  margin: 0;
  padding: 0;
}
.layout-container {
  height: 100vh;
}
</style>

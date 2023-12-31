import { createRouter, createWebHistory } from 'vue-router'
import HomePage from './../views/Sample.vue'
import AdminPage from './../views/Admin.vue'


const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage
    },
    {
      path : '/admin',
      component : AdminPage,
      meta : {
        requiresAuth : true ,
        roles : ['admin']
      }
    },
  ],
});

router.beforeEach((to,from,next) => {

    console.log(localStorage.getItem('token'));
    if(to.matched.some(record => record.meta.requiresAuth)) {
      const role = localStorage.getItem('role')
      const allowedroles = to.meta.roles;

      if(!allowedroles.includes(role)) {
        next('/register');
      } else {
        next();
      }

    }
  
  else {
    console.log('elsed');
    next();
  }
});

export default router;
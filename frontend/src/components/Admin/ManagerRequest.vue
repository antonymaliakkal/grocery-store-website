<script setup>
import { onMounted } from "vue";
import { adminStore } from "../../store/adminStore";

onMounted(() => {
  adminStore.getManagerRequests();
});
</script>
<template>
  <div class="mb-3">
    <h3 class="text-left mb-0">Pending Manager Approvals</h3>
    <div v-if="Object.keys(adminStore.managerRequests || {}).length <= 0">
      <p class="text-left">No pending manager requests</p>
    </div>
    <div class="card-deck">
      <div
        class="card bg-dark text-white"
        v-for="(value, key) in adminStore.managerRequests"
        :key="key"
      >
        <!-- <img class="card-img-top" src="..." alt="Card image cap" /> -->
        <div class="card-body">
          <h5 class="card-title">{{ value }}</h5>
          <div class="d-flex justify-content-center" style="gap: 10px">
            <button
              class="btn btn-outline-danger btn-sm"
              @click="adminStore.rejectManagerRequest(key)"
            >
              Reject
            </button>
            <button
              class="btn btn-success btn-sm"
              @click="adminStore.approveManagerRequest(key)"
            >
              Approve
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

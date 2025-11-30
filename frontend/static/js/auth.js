// Auto close flash messages after 4 seconds
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(el => {
      const alertInstance = bootstrap.Alert.getOrCreateInstance(el);
      alertInstance.close();
    });
  }, 4000);
});

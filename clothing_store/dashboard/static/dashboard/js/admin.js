// ================= SIDEBAR TOGGLE =================
document.addEventListener("DOMContentLoaded", function () {
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  const mainContent = document.getElementById("mainContent");

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("active");

      // On mobile, toggle sidebar visibility
      if (window.innerWidth <= 768) {
        if (sidebar.style.transform === "translateX(0px)") {
          sidebar.style.transform = "translateX(-100%)";
        } else {
          sidebar.style.transform = "translateX(0)";
        }
      }
    });
  }

  // Close sidebar on mobile when clicking outside
  document.addEventListener("click", function (event) {
    if (window.innerWidth <= 768) {
      if (
        !sidebar.contains(event.target) &&
        !sidebarToggle.contains(event.target)
      ) {
        sidebar.style.transform = "translateX(-100%)";
      }
    }
  });
});

// ================= DELETE CONFIRMATION =================
function confirmDelete(itemName) {
  return confirm(
    `Are you sure you want to delete "${itemName}"? This action cannot be undone.`
  );
}

// ================= FORM VALIDATION =================
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return true;

  const requiredFields = form.querySelectorAll("[required]");
  let isValid = true;

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      field.classList.add("is-invalid");
      isValid = false;
    } else {
      field.classList.remove("is-invalid");
    }
  });

  return isValid;
}

// ================= AUTO-DISMISS ALERTS =================
setTimeout(function () {
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    const bsAlert = new bootstrap.Alert(alert);
    setTimeout(() => {
      bsAlert.close();
    }, 5000);
  });
}, 100);

// ================= SEARCH FUNCTIONALITY =================
function searchTable(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);

  if (!input || !table) return;

  input.addEventListener("keyup", function () {
    const filter = input.value.toLowerCase();
    const rows = table.getElementsByTagName("tr");

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const text = row.textContent.toLowerCase();

      if (text.includes(filter)) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    }
  });
}

// ================= IMAGE PREVIEW =================
function previewImage(input, previewId) {
  const preview = document.getElementById(previewId);
  if (!preview) return;

  if (input.files && input.files[0]) {
    const reader = new FileReader();

    reader.onload = function (e) {
      preview.src = e.target.result;
      preview.style.display = "block";
    };

    reader.readAsDataURL(input.files[0]);
  }
}

// ================= AJAX STATUS UPDATE =================
function updateStatus(url, statusValue, elementId) {
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ status: statusValue }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Update UI
        const element = document.getElementById(elementId);
        if (element) {
          element.textContent = statusValue;
        }

        // Show success message
        showToast("Status updated successfully!", "success");
      } else {
        showToast("Failed to update status", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast("An error occurred", "error");
    });
}

// ================= GET CSRF TOKEN =================
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ================= TOAST NOTIFICATIONS =================
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
  toast.style.zIndex = "9999";
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}

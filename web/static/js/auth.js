$(function () {
  // ---- Helpers -----------------------------------------------------
  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : null;
  }

  function setInvalid($input, message) {
    $input.addClass('is-invalid');
    $input.siblings('.invalid-feedback').text(message || 'Invalid value');
  }

  function clearInvalid($form) {
    $form.find('.is-invalid').removeClass('is-invalid');
    $form.find('.invalid-feedback').text('');
    $form.find('.alert').addClass('d-none').text('');
  }

  function postJSON(url, data, csrfToken) {
    return $.ajax({
      url: url,
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(data),
      headers: { 'X-CSRF-Token': csrfToken || '' },
      xhrFields: { withCredentials: true }
    });
  }

  // ---- Signup ------------------------------------------------------
  $('#signupForm').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    clearInvalid($form);

    const data = {
      first_name: $form.find('[name="first_name"]').val().trim(),
      last_name: $form.find('[name="last_name"]').val().trim(),
      email: $form.find('[name="email"]').val().trim(),
      password: $form.find('[name="password"]').val()
    };

    if (data.password.length < 8) {
      setInvalid($form.find('[name="password"]'), 'Password must be at least 8 characters.');
      return;
    }

    const csrf = getCookie('csrf_token');
    postJSON('/api/signup', data, csrf)
      .done(function (res) {
        if (res.ok) {
          window.location.href = res.redirect || '/';
        } else {
          const $alert = $('#signupFormAlert');
          let shownTopAlert = false;
          res.errors.forEach(err => {
            const $input = $form.find(`[name="${err.field}"]`);
            if ($input.length) {
              setInvalid($input, err.message);
            } else if (!shownTopAlert) {
              $alert.text(err.message).removeClass('d-none');
              shownTopAlert = true;
            }
          });
        }
      })
      .fail(function () {
        $('#signupFormAlert').text('Network error. Please try again.').removeClass('d-none');
      });
  });

  // ---- Signin ------------------------------------------------------
  $('#signinForm').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    clearInvalid($form);

    const data = {
      email: $form.find('[name="email"]').val().trim(),
      password: $form.find('[name="password"]').val()
    };

    const csrf = getCookie('csrf_token');
    postJSON('/api/signin', data, csrf)
      .done(function (res) {
        if (res.ok) {
          window.location.href = res.redirect || '/';
        } else {
          const $alert = $('#signinFormAlert');
          let hasFormError = false;
          res.errors.forEach(err => {
            if (err.field === 'form') {
              $alert.text(err.message).removeClass('d-none');
              hasFormError = true;
            }
          });
          if (!hasFormError) {
            res.errors.forEach(err => {
              const $input = $form.find(`[name="${err.field}"]`);
              if ($input.length) setInvalid($input, err.message);
            });
          }
        }
      })
      .fail(function () {
        $('#signinFormAlert').text('Network error. Please try again.').removeClass('d-none');
      });
  });
});

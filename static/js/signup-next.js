$("select").on("select2:clear", function (evt) {
  $(this).on("select2:opening.cancelOpen", function (evt) {
    evt.preventDefault();

    $(this).off("select2:opening.cancelOpen");
  });
});

$(".next").on('click', function () {
  const form = $('#form')
  if (form[0].reportValidity()) {
    const current = form.find('.visible')
    if (current.not(':last-child')) {
      const next = current.removeClass('visible').next()
      next.addClass('visible')
      $('.progressbar').find('.active:not(:last-child)').removeClass('active').next().addClass('active')
      $('.back').show()
      if (next.is(':last-child')) {
        $(this).hide()
        $('.save').show()
        if ($(window).height() < 610) {
          $('.nav-buttons').css("width", "250px")
          $('.nav-buttons').css("margin", "auto")
        }
      }
    }
  }
})

$(".back").on('click', function () {
  const form = $('#form')
  if (form[0].reportValidity()) {
    const current = form.find('.visible')
    if (current.not(':first-child')) {
      const prev = current.removeClass('visible').prev()
      prev.addClass('visible')
      $('.nav-buttons').css('width', 'auto')
      $('.nav-buttons').css('margin', '0')
      $('.save').hide()
      $('.next').show()
      $('.progressbar').find('.active:not(:first-child)').removeClass('active').prev().addClass('active').not(':first-child')
      if (prev.is(':first-child')) {
        $(this).hide()
      }
    }
  }
})
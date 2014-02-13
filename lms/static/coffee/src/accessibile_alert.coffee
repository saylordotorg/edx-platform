
class SRAlert
  constructor: ->
    $('body').append('<div id="reader-feedback" class="sr" style="display:none" aria-hidden="false" aria-atomic="true" aria-live="assertive"></div>')
    @el = $('#reader-feedback')

  clear: ->
    @el.html(' ')

  readElts: (elts) ->
    feedback = ''
    $.each elts, (idx, value) =>
      feedback += '<p>' + $(value).html() + '</p>\n'
    @el.html(feedback)

  readText: (text) ->
    @el.text(text)


window.SR = new SRAlert

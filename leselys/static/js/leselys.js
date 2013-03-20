function addSubscription() {
  var url = $('#urlSubscription').val();
  if (url == '') {
    return false;
  }

  // Clear help message if no subscriptions
  if ($("ul#menu li#empty-feed-list").length) {
    $("ul#menu li#empty-feed-list").hide();
    $("ul#menu li#listSubscriptions").show();
  }
  var loader = crel('li', crel('i', {'class': 'icon-tasks'}), ' Loading...');
  document.getElementById('menu').appendChild(loader);
  $.post('/api/add', {url: url}, function(data) {
    if (data.success == true) {
      /////////////////////////////////////
      // Go login page if not connected ///
      if ($(data).find('.form-signin').length > 0) {
        window.location = "/login";
      }
      /////////////////////////////////////
      $(loader).hide();
      $(loader).html('<a onClick="viewSubscription(&quot;' + data.feed_id + '&quot;)" href="/#' + data.feed_id + '">' + data.title + ' <span id="unread-counter" class="badge badge-inverse">' + data.counter  + '</span></a>').fadeIn();
      $(loader).attr('id', data.feed_id);
      $(loader).addClass('story');
      // Add new feed in settings/feeds if opened
      if ($('#settings.tab-pane').length > 0) {
        // Remove message if feeds list is empty
        if ($('#feeds.tab-pane #empty-feed-list').length > 0) {
          $('#feeds.tab-pane #empty-feed-list').hide();
        }
        $('#feeds.tab-pane ul').append('<li id="' +  data.feed_id + '">' + data.title + ' <a onClick="delSubscription(&quot;' + data.feed_id + '&quot;);" href="#">(delete)</a></li>');
      }
    } else {
      /////////////////////////////////////
      // Go login page if not connected ///
      if ($(data).find('.form-signin').length > 0) {
        window.location = "/login";
      }
      /////////////////////////////////////
      $(loader).html('<li><i class="icon-exclamation-sign"></i> Error: ' + data.output +'</li>');
      var clearLoader = function() {
        $(loader).fadeOut();
      }
      setTimeout(clearLoader, 5000);
    }
  });
  $('#add').popover('hide')
}

function handleOPMLImport(evt) {
  if ($('#import-export #upload-file-info').html() == "") {
    return false;
  }
  if (importer) {
    return false;
  }
  // Check if browser is FileRead object compatible
  if (window.File && window.FileReader && window.FileList && window.Blob) {
    // Great success! All the File APIs are supported.
  } else {
    alert('The File APIs are not fully supported in this browser.');
    return false;
  }

  // Retrieve file from form
  importer = true;
  var file = document.getElementById('OPMLFile').files[0]
  if (!file) { return false }
  var reader = new FileReader();

  reader.onload = (function(OPMLFile) {
    return function(e) {
      $.post('/api/import/opml', { file: e.target.result }, function(data) {
        /////////////////////////////////////
        // Go login page if not connected ///
        if ($(data).find('.form-signin').length > 0) {
          window.location = "/login";
        }
        /////////////////////////////////////
        if (data.success == true) {
          importer = false;
          $('#OPMLSubmit').html('Importing, reload page later...');
          $('#OPMLSubmit').addClass('disabled');
        }
      });
    }
  })(file);
  reader.readAsText(file);
}

function viewSettings() {
  $.get('/settings', function(body) {
    /////////////////////////////////////
    // Go login page if not connected ///
    if ($(body).find('.form-signin').length > 0) {
      window.location = "/login";
    }
    /////////////////////////////////////
    var content = $(body).find('#content');
    var sidebar = $(body).find('#menu')
    $('#content').html(content.html());
    $('#menu').html(sidebar.html());
    if (importer) {
      $('#OPMLSubmit').html('Last import not finished...');
      $('#OPMLSubmit').addClass('disabled');
      return false;
    }
    if ($('#OPMLSubmit').length > 0) {
      document.getElementById('OPMLSubmit').addEventListener('click', handleOPMLImport, false);
    }
    initAddSubscription();
  });
}

function viewHome() {
  $.get('/', function(body) {
    /////////////////////////////////////
    // Go login page if not connected ///
    if ($(body).find('.form-signin').length > 0) {
      window.location = "/login";
    }
    /////////////////////////////////////
    var content = $(body).find('#content');
    var sidebar = $(body).find('#menu')
    $('#content').html(content.html());
    $('#menu').html(sidebar.html());
    initAddSubscription();
  });
}

function delSubscription(feedId) {
  $.ajax({
    url: '/api/remove/' + feedId,
    type: 'DELETE',
    success: function(result) {
      /////////////////////////////////////
      // Go login page if not connected ///
      if ($(result).find('.form-signin').length > 0) {
        window.location = "/login";
      }
      /////////////////////////////////////
      $('#feeds ul li#' + feedId).fadeOut(300, function() {
        $(this).remove();
        if ($('#feeds ul li').length < 1) {
          $('#feeds.tab-pane #empty-feed-list').fadeIn(200);
        }
      });
      $('ul#menu li#' + feedId).fadeOut(300, function() {
        $(this).remove();
        if ($('ul#menu li').length < 6) {
          $('ul#menu li#listSubscriptions.nav-header').fadeOut(200);
          $('ul#menu li#empty-feed-list').fadeIn(200);
        }
      });
    }
  });
}

function viewSubscription(feedId) {
  $.each(requests, function(i, request) {
      request.abort();
      requests.shift();
  });
  var request = $.getJSON('/api/get/' + feedId, function(data) {
    /////////////////////////////////////
    // Go login page if not connected ///
    if ($(data).find('.form-signin').length > 0) {
      window.location = "/login";
    }
    /////////////////////////////////////
    var header = '<div class="accordion" id="story-list-accordion">';
    var footer = '</div>';
    var content = '';

    $.each(data.content, function(i,item){
      var storyAccordion = getStoryAccordionTemplate();
      storyAccordion.id = 'story-list-accordion';
      storyAccordion.getElementsByClassName('accordion-toggle')[0].onclick = 'readEntry("' + item._id + '")';
      storyAccordion.getElementsByClassName('accordion-toggle')[0].setAttribute("onclick", 'readEntry("' + item._id + '")');
      storyAccordion.getElementsByClassName('accordion-toggle')[0].href = "#" + item._id;
      storyAccordion.getElementsByClassName('accordion-toggle')[0].innerHTML = item.title;
      storyAccordion.getElementsByClassName('accordion-body')[0].id = item._id;
      storyAccordion.getElementsByClassName('accordion-inner')[0].id = item._id;

      if (item.read == false) {
        storyAccordion.getElementsByClassName('accordion-toggle')[0].style.fontWeight = 'bold';
      }

      content += storyAccordion.outerHTML;
    });
    $("#content").html(header + content + footer);
    $('#menu a').each(function(index) {
      $(this).css('font-weight', 'normal');
    });
    $('#menu li#' + feedId + " a").css('font-weight', 'bold');
  });
  requests.push(request);
}

function refreshSubscriptions() {
  $.each($('#menu .story'), function(i, story) {
    var feedId = $(story).attr('id');
    $.getJSON('/api/refresh/' + feedId), function(data) {
      /////////////////////////////////////
      // Go login page if not connected ///
      if ($(data).find('.form-signin').length > 0) {
        window.location = "/login";
      }
      /////////////////////////////////////
      var feedTitle = data.content.title;
      var feedCounter = data.content.counter;
      $("#menu a[href=#" + feedId + "] span.badge").html(feedCounter);
    }
  });
}

function readEntry(entryId) {
  // Avoid "read" state if story have just been marked unread
  if ($('a[href=#' + entryId + ']').data('unreaded')) {
    $('a[href=#' + entryId + ']').data('unreaded', false);
    return true;
  }
  $.getJSON('/api/read/' + entryId, function(data) {
    /////////////////////////////////////
    // Go login page if not connected ///
    if ($(data).find('.form-signin').length > 0) {
      window.location = "/login";
    }
    /////////////////////////////////////
    if (data.content.last_update == false) {
      var published = "No date";
    } else {
      var published = data.content.last_update['year'] + '-' + data.content.last_update['month'] +
                    '-' + data.content.last_update['day'];
    }

    var story = getStoryTemplate();
    story.getElementsByClassName("story-link")[0].href = data.content.link;
    story.getElementsByClassName("story-unread")[0].onclick = 'unreadEntry("' + entryId + '")';
    story.getElementsByClassName('story-unread')[0].setAttribute("onclick", 'unreadEntry("' + entryId + '")');
    story.getElementsByClassName("story-content")[0].innerHTML = data.content.description;
    story.getElementsByClassName("story-date")[0].innerHTML = published;

    $('#content #' + entryId).html(story.outerHTML)
    if (data.success == true) {
      var feedId = data.content.feed_id;
      var counter = parseInt($("#menu li#" + feedId + " #unread-counter").html()) - 1;
      if (counter == 0) {
        $("#menu li#" + feedId + " #unread-counter").html(counter);
        $("#menu li#" + feedId + " #unread-counter").fadeOut();
      } else {
        $("#menu li#" + feedId + " #unread-counter").html(counter);
      }
    }
  });
  $('a[href=#' + entryId + ']').css('font-weight', 'normal');
}

function unreadEntry(storyId) {
  $.getJSON('/api/unread/' + storyId, function(data) {
    /////////////////////////////////////
    // Go login page if not connected ///
    if ($(data).find('.form-signin').length > 0) {
      window.location = "/login";
    }
    /////////////////////////////////////
    if (data.success == true) {
      feedId = data.content.feed_id;
      var counter = parseInt($("#menu li#" + feedId + " #unread-counter").html()) + 1;

      $('a[href=#' + storyId + ']').data('unreaded', true);
      if (counter == 1) {
        $("#menu li#" + feedId + " #unread-counter").html(counter);
        $("#menu li#" + feedId + " #unread-counter").fadeIn();
      } else {
        $("#menu li#" + feedId + " #unread-counter").html(counter);
      }
      $('a[href=#' + storyId + ']').css('font-weight', 'bold');
    }
  });
}

function initAddSubscription() {
  var addSubscription = getAddSubscriptionTemplate();
  $('#add').popover({'title': "<center>New subscription</center>",
                     'html': true,
                     'content': addSubscription.outerHTML,
                     'placement': "bottom"}
  );
}

$(document).ready(function(){
  // Globals
  // Remove anchors binding for mobile view
  $('.story').click(function(e) {
    e.preventDefault();
  });
  requests = new Array();
  importer = false;
});

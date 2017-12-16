madrona.onShow(function(){
    madrona.setupForm($('#scenarios-form'));

    $(window).on('resize', function() {
      updateDesignScrollBar();
    });

    var step = 1;
    // var max_step = {{ form.get_steps|length|add:"1" }};

    function validate(step) {
        return true;
    };

    function wizard(action) {
        if (step == 1 && action == 'next') {
            if (validate(step)) {
                step += 1;
            }
        } else if (step < max_step && action == 'next') {
            step += 1;
        } else if (step > 1 && action == 'prev') {
            step -= 1;
        }
        if (step === max_step) {
            if ( app.viewModel.scenarios.scenarioFormModel.gridCellsRemaining() === 0) {
                $('#empty-results-warning').effect("highlight", {}, 1000);
            }
        }
        $('div.step').each(function(index) {
            $(this).hide();
        });
        $('div#step' + step).show();
        updateDesignScrollBar();
        $('#scenarios-form').data('jsp').scrollTo(0,0);


        if (step == 1) {
            $('#button_prev').hide();
            $('#button_next').css('border-radius', '4px');
        } else {
            $('#button_prev').show();
            $('#button_next').css('border-top-right-radius', '4px');
            $('#button_next').css('border-bottom-right-radius', '4px');
            $('#button_next').css('border-top-left-radius', '0px');
            $('#button_next').css('border-bottom-left-radius', '0px');
        }

        if (step == max_step) {
            $('#button_next').hide();
            if ( app.viewModel.scenarios.scenarioFormModel.gridCellsRemaining() != 0 ) {
                $('.submit_button').show();
            }
        } else {
            $('#button_next').show();
            $('.submit_button').hide();
        }
    };

    function showhide_widget(element) {
        element.fadeToggle(100); //slideToggle
    }

    function updateRemainingLeaseBlocks() {
        app.viewModel.scenarios.scenarioFormModel.updateLeaseblocksLeft();
        app.viewModel.scenarios.scenarioFormModel.updateRemainingBlocks();
    }

    function updateDesignScrollBar() {
        var designsWizardScrollpane = $('#wind-design-form').data('jsp');
        if (designsWizardScrollpane === undefined) {
            $('#wind-design-form').jScrollPane();
        } else {
            setTimeout(function() {designsWizardScrollpane.reinitialise();},200);
        }
    };

    updateDesignScrollBar();
    wizard();

    $('.inputfield').each(function() {
        $(this).hide();
    });

    $('#button_prev').click( function() { wizard('prev'); });
    $('#button_next').click( function() { wizard('next'); });

    $('ul.errorlist').each( function() {
        step = max_step;
        wizard();
    });


    if ($("input[type='color']").length) {
        $.getScript("media/marco/js/mColorPicker.js");
    }

    $('#id_name').keypress(function (e) {
        if (e.which === 13) {
            $('#scenario-form .submit_button').click();
            return false;
        } else {
            $('#invalid-name-message').hide();
        }
    });
    var slidervalueElements = document.getElementsByClassName('slidervalue');
    for (var i=0; i<slidervalueElements.length; i+=1) {
        slidervalueElements[i].addEventListener('keypress', function(event) {
            if (event.keyCode == 13) {
                event.preventDefault();
                $(event.currentTarget).blur();
            }
        });
    }

    /* Tooltips */
    //overriding the template here to remove empty space for title
    $('.info-icon').popover({
        trigger: 'hover',
        template: '<div class="popover layer-popover"><div class="arrow"></div><div class="popover-inner layer-tooltip"><div class="popover-content"><p></p></div></div></div>'
    });
    $('.info-icon').click(function(e) {
        if ( $('.popover').is(':visible') ) {
            $('.popover').hide();
        }
    });
    $('.disabled-grid-button').popover({
        trigger: 'hover',
        template: '<div class="popover layer-popover"><div class="arrow"></div><div class="popover-inner layer-tooltip"><div class="popover-content"><p></p></div></div></div>'
        // html: 'true'
    });
});

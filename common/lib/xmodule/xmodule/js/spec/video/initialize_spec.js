(function (requirejs, require, define, undefined) {

'use strict';

require(
['video/01_initialize.js'],
function (Initialize) {
    describe('Initialize', function () {
        var state = {};

        afterEach(function () {
            state = {};
        });

        describe('saveState function', function () {
            var videoPlayerCurrentTime, newCurrentTime, speed;

            // We make sure that `currentTime` is a float. We need to test
            // that Math.round() is called.
            videoPlayerCurrentTime = 3.1242;

            // We have two times, because one is  stored in
            // `videoPlayer.currentTime`, and the other is passed directly to
            // `saveState` in `data` object. In each case, there is different
            // code that handles these times. They have to be different for
            // test completeness sake. Also, make sure it is float, as is the
            // time above.
            newCurrentTime = 5.4;

            speed = '0.75';

            beforeEach(function () {
                state = {
                    videoPlayer: {
                        currentTime: videoPlayerCurrentTime
                    },
                    storage: {
                        setItem: jasmine.createSpy()
                    },
                    config: {
                        saveStateUrl: 'http://example.com/save_user_state'
                    }
                };

                spyOn($, 'ajax');
                spyOn(Time, 'formatFull').andCallThrough();
            });

            it('data is not an object, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: videoPlayerCurrentTime,
                    data: undefined,
                    ajaxData: {
                        saved_video_position: Time.formatFull(Math.round(videoPlayerCurrentTime))
                    }
                });
            });

            it('data contains speed, async is false', function () {
                itSpec({
                    asyncVal: false,
                    speedVal: speed,
                    positionVal: undefined,
                    data: {
                        speed: speed
                    },
                    ajaxData: {
                        speed: speed
                    }
                });
            });

            it('data contains float position, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: newCurrentTime,
                    data: {
                        saved_video_position: newCurrentTime
                    },
                    ajaxData: {
                        saved_video_position: Time.formatFull(Math.round(newCurrentTime))
                    }
                });
            });

            it('data contains speed and rounded position, async is false', function () {
                itSpec({
                    asyncVal: false,
                    speedVal: speed,
                    positionVal: Math.round(newCurrentTime),
                    data: {
                        speed: speed,
                        saved_video_position: Math.round(newCurrentTime)
                    },
                    ajaxData: {
                        speed: speed,
                        saved_video_position: Time.formatFull(Math.round(newCurrentTime))
                    }
                });
            });

            it('data contains empty object, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: undefined,
                    data: {},
                    ajaxData: {}
                });
            });

            it('data contains position 0, async is true', function () {
                itSpec({
                    asyncVal: true,
                    speedVal: undefined,
                    positionVal: 0,
                    data: {
                        saved_video_position: 0
                    },
                    ajaxData: {
                        saved_video_position: Time.formatFull(Math.round(0))
                    }
                });
            });

            return;

            function itSpec(value) {
                var asyncVal    = value.asyncVal,
                    speedVal    = value.speedVal,
                    positionVal = value.positionVal,
                    data        = value.data,
                    ajaxData    = value.ajaxData;

                Initialize.prototype.saveState.call(state, asyncVal, data);

                if (speedVal) {
                    expect(state.storage.setItem).toHaveBeenCalledWith(
                        'speed',
                        speedVal,
                        true
                    );
                }
                if (positionVal) {
                    expect(state.storage.setItem).toHaveBeenCalledWith(
                        'savedVideoPosition',
                        positionVal,
                        true
                    );
                    expect(Time.formatFull).toHaveBeenCalledWith(
                        positionVal
                    );
                }
                expect($.ajax).toHaveBeenCalledWith({
                    url: state.config.saveStateUrl,
                    type: 'POST',
                    async: asyncVal,
                    dataType: 'json',
                    data: ajaxData
                });
            }
        });

        describe('getCurrentLanguage', function () {
            beforeEach(function () {
                state.config = {};
                state.config.transcriptLanguages = {
                    'de': 'German',
                    'en': 'English',
                };
            });

            it ('returns current language', function () {
                var expected;

                state.lang = 'de';
                expected = Initialize.prototype.getCurrentLanguage.call(state);
                expect(expected).toBe('de');
            });

            var msg = 'returns `en`, if language isn\'t available for the video';
            it (msg, function () {
                var expected;

                state.lang = 'zh';
                expected = Initialize.prototype.getCurrentLanguage.call(state);
                expect(expected).toBe('en');
            });
        });

        describe('getDuration', function () {
            beforeEach(function () {
                state = {
                    speed: '1.50',
                    metadata: {
                        'testId': {
                            duration: 400
                        },
                        'videoId': {
                            duration: 100
                        }
                    },
                    videos: {
                        '1.0': 'testId',
                        '1.50': 'videoId'
                    },
                    youtubeId: Initialize.prototype.youtubeId
                };
            });

            it('returns duration for current video', function () {
                var expected = Initialize.prototype.getDuration.call(state);

                expect(expected).toEqual(100);
            });

            var msg = 'returns duration for the 1.0 speed if metadata for ' +
                        'videoId doesn\'t exist';
            it(msg, function () {
                var expected;

                state.speed = '2.0';
                expected = Initialize.prototype.getDuration.call(state);

                expect(expected).toEqual(400);
            });
        });

        describe('youtubeId', function () {
            beforeEach(function () {
                state = {
                    speed: '1.50',
                    videos: {
                        '0.50': '7tqY6eQzVhE',
                        '1.0': 'cogebirgzzM',
                        '1.50': 'abcdefghijkl'
                    }
                };
            });

            describe('with speed', function () {
                it('return the video id for given speed', function () {
                    $.each(state.videos, function(speed, videoId) {
                        var expected = Initialize.prototype.youtubeId.call(
                                state, speed
                            );

                        expect(videoId).toBe(expected);
                    });
                });
            });

            describe('without speed', function () {
                it('return the video id for current speed', function () {
                    var expected = Initialize.prototype.youtubeId.call(state);

                    expect(expected).toEqual('abcdefghijkl');
                });
            });

            describe('speed is absent in the list of video speeds', function () {
                it('return the video id for 1.0x speed', function () {
                    var expected = Initialize.prototype.youtubeId.call(state, '0.0');

                    expect(expected).toEqual('cogebirgzzM');
                });
            });
        });

        describe('setSpeed', function () {
            describe('YT', function () {
                beforeEach(function () {
                    state = {
                        speeds: ['0.25', '0.50', '1.0', '1.50', '2.0'],
                        storage: jasmine.createSpyObj('storage', ['setItem'])
                    };
                });

                it('check mapping', function () {
                    var map = {
                        '0.75': '0.50',
                        '1.25': '1.50'
                    };

                    $.each(map, function(key, expected) {
                        Initialize.prototype.setSpeed.call(state, key);
                        expect(state.speed).toBe(expected);
                    });
                });
            });

            describe('HTML5', function () {
                beforeEach(function () {
                    state = {
                        speeds: ['0.75', '1.0', '1.25', '1.50'],
                        storage: jasmine.createSpyObj('storage', ['setItem'])
                    };
                });

                describe('when new speed is available', function () {
                    beforeEach(function () {
                        Initialize.prototype.setSpeed.call(state, '0.75', true);
                    });

                    it('set new speed', function () {
                        expect(state.speed).toEqual('0.75');
                    });

                    it('save setting for new speed', function () {
                        expect(state.storage.setItem.calls[0].args)
                            .toEqual(['speed', '0.75', true]);

                        expect(state.storage.setItem.calls[1].args)
                            .toEqual(['general_speed', '0.75']);
                    });
                });

                describe('when new speed is not available', function () {
                    beforeEach(function () {
                        Initialize.prototype.setSpeed.call(state, '1.75');
                    });

                    it('set speed to 1.0x', function () {
                        expect(state.speed).toEqual('1.0');
                    });
                });

                it('check mapping', function () {
                    var map = {
                        '0.25': '0.75',
                        '0.50': '0.75',
                        '2.0': '1.50'
                    };

                    $.each(map, function(key, expected) {
                        Initialize.prototype.setSpeed.call(state, key, true);
                        expect(state.speed).toBe(expected);
                    });
                });
            });
        });
    });
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));

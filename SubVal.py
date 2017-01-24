import sublime, sublime_plugin, re

class SubVal(sublime_plugin.EventListener):

    def on_post_save(self, view):
        self.view = view
        if self.is_subtitle_file():
            self.timing_pattern = self.get_timing_pattern()
            self.error_messages = self.get_error_messages()
            file_contents = self.get_file_contents()
            self.show_errors(self.get_timing_errors_with_loc(file_contents))

    def is_subtitle_file(self):
        file_extension = self.get_file_extension()
        return file_extension == 'srt' or file_extension == 'txt'

    def get_file_extension(self):
        file_name = self.view.file_name()
        starting_index = file_name.rfind('.')
        file_extension = file_name[starting_index + 1:].lower()
        return file_extension

    def get_file_contents(self):
        return self.view.substr(
            sublime.Region(0, self.view.size()))

    def get_timing_pattern(self):
        return re.compile('((\d+:?)+,\d+) --> ((\d+:?)+,\d+)')

    def get_timing_errors_with_loc(self, file_contents):
        timing_errors_with_loc = []
        timing_matches = self.get_timing_matches(file_contents)
        prev_timing_match = None

        for curr_timing_match in timing_matches:
            if prev_timing_match == None:
                prev_timing_match = curr_timing_match
                continue
            self.add_timing_error_with_loc(prev_timing_match,
                curr_timing_match, file_contents, timing_errors_with_loc)
            prev_timing_match = curr_timing_match

        return timing_errors_with_loc

    def get_timing_matches(self, file_contents):
        return re.finditer(self.timing_pattern, file_contents)

    def add_timing_error_with_loc(self, prev_timing_match, curr_timing_match,
        file_contents, timing_errors_with_loc):
        timing_error = self.get_timing_error(
            prev_timing_match, curr_timing_match)

        if timing_error != 0:
            timing_error_loc = self.get_erroneous_timing_loc(
                curr_timing_match, file_contents)
            timing_errors_with_loc.append(
                [timing_error, timing_error_loc[0], timing_error_loc[1]])

    def get_timing_error(self, prev_timing, curr_timing):
        timings = self.seperate_timings(prev_timing, curr_timing)

        if self.compare_times(timings[0], timings[1]) < 0:
            if self.compare_times(timings[1], timings[2]) < 0:
                if self.compare_times(timings[2], timings[3]) < 0:
                    return 0
                else:
                    return 1
            else:
                return 2
        else:
            return 3

    def seperate_timings(self, prev_timing, curr_timing):
        timings = [self.get_starting_time(prev_timing), self.get_ending_time(prev_timing), self.get_starting_time(curr_timing), self.get_ending_time(curr_timing)]
        return timings

    def get_starting_time(self, timing):
        return timing.group(1)

    def get_ending_time(self, timing):
        return timing.group(3)

    def compare_times(self, time1, time2):
        numerical_time_1 = self.time_to_numerical(time1)
        numerical_time_2 = self.time_to_numerical(time2)
        return numerical_time_1 - numerical_time_2

    def time_to_numerical(self, time):
        return float(time.replace(':', '').replace(',', '.'))

    def get_erroneous_timing_loc(self, timing_match, file_contents):
        line_number = self.view.rowcol(
            file_contents.index(timing_match.group(0)))[0] + 1
        character_index = file_contents.index(timing_match.group(0))
        return (line_number, character_index)

    def get_error_messages(self):
        return {
            1: 'Current subtitle starts after it ends at line {}',
            2: 'Previous subtitle ends after current one starts at line {}',
            3: 'Previous subtitle starts after it ends at line {}'}

    def show_errors(self, errors):
        if len(errors) > 0:
            for e in errors:
                sublime.error_message(
                    self.error_messages.get(e[0]).format(e[1]))
                self.go_to_loc(e[2])
                break
        else:
            sublime.error_message('No errors were found')

    def go_to_loc(self, loc):
        self.view.show_at_center(sublime.Region(loc))
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(loc))

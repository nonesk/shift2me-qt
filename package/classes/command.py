import os
from cmd2 import Cmd, options, make_option
from classes.Titration import Titration
from tabulate import tabulate

class ShiftShell(Cmd):
    """ Command line interface wrapper for Titration
    """
    intro = "Type help or ? to list commands.\n"
    prompt = ">> "

    def __init__(self, *args, **kwargs):
        self.cutoff=None
        self.allow_cli_args = False

        self.titration =  kwargs.get('titration')

        # environment attributes
        self.name = self.titration.name
        Cmd.__init__(self)
        self._set_prompt()

        # Exclude irrelevant cmds from help menu
        self.exclude_from_help += [ 'do__relative_load',
                                    'do_cmdenvironment',
                                    'do_edit',
                                    'do_run' ]

        # Set path completion for save/load
        self.complete_save_job=self.path_complete
        self.complete_load_job=self.path_complete
        self.complete_add_step=self.path_complete
        self.complete_concentrations=self.path_complete
        self.complete_make_init=self.path_complete
        self.complete_init=self.path_complete
        self.complete_update=self.path_complete

        self.intro = "\n".join([  "\n\n\tWelcome to Shift2Me !",
                                "{summary}\n{intro}".format(
                                    summary=self.titration.summary,
                                    intro=self.intro)])


## --------------------------------------------
##      COMMANDS
## --------------------------------------------

    def do_set_name(self, arg):
        "Set titration name."
        if arg:
            self.titration.set_name(arg)
            self.name = arg
            self._set_prompt()

## PROTOCOLE CMDS -----------------------------
    @options([], arg_desc="<vol (µL)> <vol (µL)> ...")
    def do_set_volumes(self, arg, opts=None):
        "Set added titrant volumes for current titration, replacing existing volumes."
        if not arg:
            self.do_help('set_volumes')
        else:
            volumes = list(map(float, arg))
            self.titration.protocole.set_volumes(volumes)
            self.pfeedback(self.titration.protocole['vol_add'])

    @options([], arg_desc="<vol(µL)> [<vol(µL)> ...]")
    def do_add_volumes(self, arg, opts=None):
        "Add volumes to currently existing volumes in titration."
        if arg:
            volumes = list(map(float, arg))
            self.titration.protocole.add_volumes(volumes)
            self.pfeedback("Volumes are now : {volumes} (µM).".format(volumes = self.titration.protocole.volumes))
        else:
            self.do_help("add_volumes")

    @options([], arg_desc="> [<path/to/file.csv>]")
    def do_csv(self, arg, opts=None):
        """Prints each titration step experimental conditions, such as volumes and concentration of each molecule.
        Format is comma-separated CSV table. You may redirect its output :
         $ csv > path/to/file.csv
        """
        if self.titration.protocole.isInit:
            self.titration.protocole.to_csv(self.stdout, index=True)
        else:
            self.pfeedback("Titration parameters are not set. Please load a protocole file.")
            self.pfeedback("See `help init`")

    def do_status(self, arg):
        "Output titration parameters, and current status of protocole."
        protocole = self.titration.protocole
        if protocole.isInit:
            self.poutput("\n".join(["------- Titration --------------------------",
                                    " >\t{name}".format(name=protocole.name),
                                    "------- Initial parameters -----------------",
                                    "[{name}] :\t{concentration} µM".format(
                                        **protocole.titrant),
                                    "[{name}] :\t{concentration} µM".format(
                                        **protocole.analyte),
                                    "{name} volume  :\t{volume} µL".format(
                                        **protocole.analyte,
                                        volume=protocole.analyteStartVol),
                                    "Initial volume :\t{volume} µL\n".format(
                                        volume=protocole.startVol),
                                    "------- Current status ---------------------\n\n"]))
            self.poutput(tabulate(protocole.df, headers='keys', tablefmt='psql'))
        else:
            self.pfeedback("Titration parameters are not set. Please load a protocole file.")
            self.pfeedback("See `help init`")

    def do_dump_protocole(self, arg):
        """Output titration parameters in a YAML formatted file.
        Argument may be a file path to write into.
        Defaults to a YAML file named as your titration is.
        """
        if not arg or os.path.isdir(arg):
            path = os.path.join(arg, '{titration}.yml'.format(titration=self.titration.name))
        elif not arg.endswith(".yml"):
            path = arg + ".yml"
        else:
            path = arg
        self.titration.protocole.dump_init_file(path)
        self.pfeedback("Dumped titration protocole at : {path}".format(path=path))

    @options([], arg_desc='<protocole>.yml')
    def do_init(self, initFile, opts=None):
        """Loads a YAML formatted file.yml describing titration protocole.
        To generate a template protocole descriptor as <file> :
            $ dump_protocole <file>.yml
        """
        if not initFile:
            self.do_help('init')
            return
        initFile = " ".join(initFile) # ugly fix for cmd2 bad path completion
        self.pfeedback("Loading protocole from {path}.".format(path = initFile))
        try:
            self.titration.load_init_path(initFile)
        except Exception as error:
            self.pfeedback(error)
            return
        self.pfeedback("Done. Use `status` command to show protocole details.")

## RMN ANALYSIS CMDS ---------------------------------

    @options([], arg_desc='[ <directory> | <titration_file.list> ... ]')
    def do_update(self, arg, opts=None):
        """Update titration from <source>.
        If source is a directory, will add all the .list files.
        with appropriate naming regarding expected next steps.
        If source is a list of files, add all the files,
        checking they have correct name regarding expected steps.
        No argument uses directory from first invocation, looking for
        any new step .list files in it.
        Already loaded files are ignored.
        """
        try:
            files = self.titration.update(arg)
            if files:
                self.pfeedback("Updated titration steps with new data from files : ")
                for updateFile in files:
                    self.pfeedback(" + {file}".format(file=updateFile))
            else:
                self.pfeedback("Nothing to update.")
        except Exception as error:
            self.pfeedback(error)
            return

    @options([make_option('-v', '--volume', help="Volume of titrant solution to add titration step")],arg_desc='<titration_file_##.list>')
    def do_add_step(self, arg, opts=None):
        """Add a titration file as next step. Associate a volume to this step with -v option.
        Example : add_step titration_10.list -v 10
        """
        if arg:
            self.titration.add_step(arg[0], opts.volume)
        else:
            self.do_help("add_step")

    def do_save_job(self, arg):
        """Save active titration to binary pickle formatted file.
         Argument may be a file path to write into.
         Invocation with no argument saves to a pickle formatted file named as your titration is.
         """
        if not arg or os.path.isdir(arg):
            path = os.path.join(arg, '{titration}.pkl'.format(titration=self.titration.name))
        elif not arg.endswith(".pkl"):
            path = arg + ".pkl"
        else:
            path = arg
        self.titration.save(path)
        self.pfeedback("Saved job at : {path}.".format(path = path))

    def do_load_job(self, arg):
        "Load previously saved titration in pickle format, replacing active titration."
        self.pfeedback('Loading titration from : {source}'.format(source=arg))
        try:
            self.titration.load(arg)
            self.pfeedback('Now working on : {titration}'.format(titration=self.titration.name))
        except:
            return

    @options([], arg_desc="( filtered | selected | complete | incomplete )")
    def do_residues(self, args, opts=None):
        "Output residues number from predifined sets to standard output."
        argMap = {
            "filtered" : self.titration.filtered,
            "selected" : self.titration.selected,
            "complete" : self.titration.complete,
            "incomplete" : self.titration.incomplete
        }
        if not args:
            self.poutput("\t".join(list(argMap)))
            return
        for arg in args:
            try:
                if arg not in argMap:
                    raise ValueError("Skipping invalid argument {arg}.".format(arg=arg))
                self.poutput(" ".join([str(res.position) for res in argMap[arg].values()]))

            except ValueError as error:
                self.pfeedback(error)
                continue

    def do_filter(self, args, opts=None):
        "Output residues having their intensity superior or equal to current cutoff."
        self.poutput(" ".join([str(pos) for pos in self.titration.filtered]))

    @options([], arg_desc="[all] [filtered] [complete] [incomplete] [positions_slice]")
    def do_select(self, args, opts=None):
        """Select a subset of residues, either from :
         - a predefined set of residues
         - 1 or more slices of residue positions, with python-ish syntax.
        Examples :
            ':100' matches positions from start to 100
            '110:117' matches positions from 100 to 117 (excluded)
            '105 112:115' matches positions 105 and 112 to 115 (excluded)
        You may mix argument types, like select filtered residues + res #100 to #110 excluded :
            >> select filtered 100:110
        Non existant residues are skipped with a warning message.
        Finally, selection is additive only, each selected element adds up to previous selection.
        If you want to clear the current selection, use deselect command.
        """
        argMap = {
            "all" : self.titration.residues,
            "filtered" : self.titration.filtered,
            "complete" : self.titration.complete,
            "incomplete" : self.titration.incomplete
        }
        selection = []
        for arg in args:
            if arg in argMap:
                args.remove(arg)
                selection += list(argMap[arg])

        selection += self.parse_residue_slice(args)
        self.titration.select_residues(*selection)


    @options([])
    def do_deselect(self, args, opts=None):
        """Remove a subset of residues from current selection, specifying either :
         - a predefined set of residues
         - 1 or more slices of residue positions, with python-ish syntax.
           e.g : ':100' matches positions from start to 100
                 '110:117' matches positions from 100 to 117 (excluded)
                 '105 112:115' matches positions 105 and 112 to 115 (excluded)
        You may mix argument types, like deselect filtered residues + res #100 to #110 excluded :
            >> deselect filtered 100:110
        Deselection will silently ignore on currently non-selected residue.
        """
        argMap = {
            "all" : self.titration.residues,
            "filtered" : self.titration.filtered,
            "complete" : self.titration.complete,
            "incomplete" : self.titration.incomplete
        }
        selection = []
        for arg in args:
            if arg in argMap:
                args.remove(arg)
                selection += list(argMap[arg])
        selection += self.parse_residue_slice(args)
        self.titration.deselect_residues(*selection)

    def do_summary(self, args):
        "Outputs a summary of current titration state."
        self.poutput(self.titration.summary)

    @options([make_option('-p', '--plot', action="store_true", help="Set cutoff and show last step histogram.")], arg_desc = '<float>')
    def do_cutoff(self, args, opts=None):
        """Set cutoff value to filter residues with high chemshift intensity.
        """
        try:
            if not args :
                self.poutput(self.titration.cutoff)
            else:
                cutoff = float(args[0])
                self.titration.set_cutoff(cutoff)
            if opts.plot:
                self.titration.plot_hist(-1)
        except (TypeError, IndexError) as error:
            self.pfeedback(error)
            self.do_help("cutoff")

## PLOTTING CMDS ------------------------------

    @options([],arg_desc='residue [residue ...]')
    def do_curve(self, arg, opts=None):
        "Show titration curve of one or several residues."
        if not arg:
            self.do_help('curve')
        elif not self.titration.protocole.isInit:
            self.pfeedback("Cannot plot titration curve : titration parameters are not set.")
            self.pfeedback("See : `help init` to load a protocole file.")
        else:
            for residue in arg:
                self.titration.plot_titration(self.titration.complete.get(int(residue)))

    @options([make_option('-e', '--export', help="Export hist as PNG image")],
            arg_desc='(<titration_step> | all)')
    def do_hist(self, args, opts=None):
        """Plot chemical shift intensity per residu as histograms.
        Accepted arguments are any titration step.
        or 'all' to plot all steps as stacked histograms.
        Invocation with no argument plots the last step.
        """
        step = args[0] if args else self.titration.dataSteps -1
        if step == 'all': # plot stacked hist
            hist = self.titration.plot_hist()
        else: # plot single hist
            hist = self.titration.plot_hist(step=int(step))

        if opts.export: # export figure as png
            hist.figure.savefig(opts.export, dpi = hist.figure.dpi)

    @options([
        make_option('-s', '--split', action="store_true", help="Sublot each residue individually"),
        make_option('-e', '--export', help="Export 2D shifts map as PNG image")
    ],
    arg_desc='( complete | filtered | selected )')
    def do_shiftmap(self, args, opts=None):
        """Plot chemical shifts for H and N atoms for each residue at all titration steps.
        """
        argMap = {
            "complete" : self.titration.complete,
            "filtered" : self.titration.filtered,
            "selected" : self.titration.selected
        }
        try:
            if not args:
                self.poutput("\t".join(list(argMap)))
                return
            if args[0] not in argMap:
                raise ValueError("Invalid argument : {arg}. Use `shiftmap -h` for help.".format(arg=args[0]))
            residues = argMap[args[0]].values()
            fig = self.titration.plot_shiftmap(residues, split=opts.split)
            if opts.export:
                fig.figure.savefig(opts.export, dpi=fig.figure.dpi)
        except ValueError as invalidArgErr:
            self.pfeedback(invalidArgErr)
            return

## --------------------------------------------
##      UTILS
## --------------------------------------------
    def parse_residue_slice(self, sliceList):
        """
        Parse a list of residue position slices
        slices are expanded the same as python slice, i.e:
            5:8 will yield 5,6,7
            5: will yield all positions from 5 to last.
        """
        selection = []
        for arg in sliceList:
            arg = arg.split(':')
            arg = [ int(subArg) if subArg else None for subArg in arg]
            if len(arg) > 1:
                if all(subArg is None for subArg in arg):
                    break
                elif arg[0] is None:
                    selection += range(min(self.titration.residues), arg[1])
                elif arg[1] is None:
                    selection += range(arg[0], max(self.titration.residues))
                else:
                    selection += range(arg[0], arg[1])
            elif len(arg) == 1:
                selection += arg
            else:
                break
        return selection

    def _set_prompt(self):
        """ Set prompt so it displays the current working directory."""
        self.cwd = os.getcwd().strip("'")
        self.prompt = self.colorize("[shift2me] ", 'magenta') + self.colorize("'"+self.name+"'", "green") + " $ "

    def postcmd(self, stop, line):
        """ Hook method executed just after a command dispatch is finished.
        :param stop: bool - if True, the command has indicated the application should exit
        :param line: str - the command line text for this command
        :return: bool - if this is True, the application will exit after this command and the postloop() will run
        """
        """Override this so prompt always displays cwd."""
        self._set_prompt()
        return stop

## --------------------------------------------------------
##    COMPLETERS
## --------------------------------------------------------

    def complete_hist(self, text, line ,begidx, endidx):
        "Completer for hist command"
        flagComplete = self.complete_flag_path('e', 'export', text, line ,begidx, endidx)
        if flagComplete: return flagComplete

        histArgs = list( map(str, self.titration.sortedSteps) ) + ['all']
        return self._complete_arg_set(text, line, histArgs)


    def complete_shiftmap(self, text, line ,begidx, endidx):
        "Completer for shiftmap command"
        flagComplete = self.complete_flag_path('e', 'export', text, line ,begidx, endidx)
        if flagComplete: return flagComplete

        residueSetArgs = ['complete', 'filtered', 'selected']
        return self._complete_arg_set(text, line, residueSetArgs)

    def complete_residues(self, text, line ,begidx, endidx):
        "Completer for shiftmap command"
        residueSetArgs = ['incomplete', 'complete', 'filtered', 'selected']
        return self._complete_arg_set(text, line, residueSetArgs)

    def complete_flag_path(self, shortFlag, longFlag, text, line ,begidx, endidx):
        # accept --flag=, flag=, --flag, flag
        longFlag = '--'+longFlag.strip('--=')+'='
        shortFlag = '-'+shortFlag.strip('-')
        if text.startswith(longFlag):
            # remove flag and start path completion
            pathText = text[len(longFlag):]
            return [longFlag + path for path in self._complete_truncated(pathText) ]

            # complete flag (this is ugly if several flags start with same letter)
        elif text.startswith(longFlag[:3]):
            return [longFlag]
        return []

    def complete_select(self, text, line ,begidx, endidx):
        "Completer for select command"
        residueSetArgs = ['incomplete', 'complete', 'filtered', 'all']
        return self._complete_arg_set(text, line, residueSetArgs)

    def complete_deselect(self, text, line ,begidx, endidx):
        return self.complete_select(text, line ,begidx, endidx)

    def _listdir(self, root):
        "List directory 'root' appending the path separator to subdirs."
        res = []
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isdir(path):
                name += os.sep
            res.append(name)
        return res

    def _complete_truncated(self, path=None):
        "Perform completion of filesystem path when inside a posix flag"
        if not path:
            return self._listdir('.')
        dirname, rest = os.path.split(path)
        tmp = dirname if dirname else '.'
        res = [os.path.join(dirname, p)
                for p in self._listdir(tmp) if p.startswith(rest)]
        # more than one match, or single match which does not exist (typo)
        if len(res) > 1 or not os.path.exists(path):
            return res
        # resolved to a single directory, so return list of files below it
        if os.path.isdir(path):
            return [os.path.join(path, p) for p in self._listdir(path)]
        # exact file match terminates this completion
        return [path + ' ']

    def _complete_arg_set(self, text, line, argSet):
        "Completion logic for commands accepting predefined set of arguments"
        # Last word is an exact match with args
        if text in argSet:
            return [text+' ']
        # Arg already provided
        for arg in argSet:
            if arg in line.split():
                return []
        # Arg matches with many allowed args
        return [ arg+' ' for arg in argSet if arg.startswith(text) ]


#!/usr/bin/env python3
# See LICENSE for details
"""
Demonstration of using Equiv_check in-code to verify equivalence
of two identical Verilog snippets.

usage:
poetry run python3 hagent/step/test_equiv_check_standalone.py
"""

from hagent.tool.equiv_check import Equiv_check


def main():
    # Two identical verilog modules named 'top'
    gold_code = """
module Counter(
    input        enable,
    input        reset,
    output [3:0] count
    );
    reg [3:0] countReg;

    // Initialize the count register
    initial begin
      countReg = 4'b0000;
    end

    // Define the counter behavior
    always @(posedge enable or posedge reset) begin
      if (reset) begin
        countReg <= 4'b0000;
      end else begin
        countReg <= countReg + 1'b1;
      end
    end

    // Connect the count register to the output
    assign count = countReg;
  endmodule
"""
    ref_code = """
// Generated by CIRCT firtool-1.62.0\n// Standard header to adapt\
  \ well known macros for register randomization.\n`ifndef RANDOMIZE\n  `ifdef RANDOMIZE_REG_INIT\n\
  \    `define RANDOMIZE\n  `endif // RANDOMIZE_REG_INIT\n`endif // not def RANDOMIZE\n\
  \n// RANDOM may be set to an expression that produces a 32-bit random unsigned value.\n\
  `ifndef RANDOM\n  `define RANDOM $random\n`endif // not def RANDOM\n\n// Users can\
  \ define INIT_RANDOM as general code that gets injected into the\n// initializer\
  \ block for modules with registers.\n`ifndef INIT_RANDOM\n  `define INIT_RANDOM\n\
  `endif // not def INIT_RANDOM\n\n// If using random initialization, you can also\
  \ define RANDOMIZE_DELAY to\n// customize the delay used, otherwise 0.002 is used.\n\
  `ifndef RANDOMIZE_DELAY\n  `define RANDOMIZE_DELAY 0.002\n`endif // not def RANDOMIZE_DELAY\n\
  \n// Define INIT_RANDOM_PROLOG_ for use in our modules below.\n`ifndef INIT_RANDOM_PROLOG_\n\
  \  `ifdef RANDOMIZE\n    `ifdef VERILATOR\n      `define INIT_RANDOM_PROLOG_ `INIT_RANDOM\n\
  \    `else  // VERILATOR\n      `define INIT_RANDOM_PROLOG_ `INIT_RANDOM #`RANDOMIZE_DELAY\
  \ begin end\n    `endif // VERILATOR\n  `else  // RANDOMIZE\n    `define INIT_RANDOM_PROLOG_\n\
  \  `endif // RANDOMIZE\n`endif // not def INIT_RANDOM_PROLOG_\n\n// Include register\
  \ initializers in init blocks unless synthesis is set\n`ifndef SYNTHESIS\n  `ifndef\
  \ ENABLE_INITIAL_REG_\n    `define ENABLE_INITIAL_REG_\n  `endif // not def ENABLE_INITIAL_REG_\n\
  `endif // not def SYNTHESIS\n\n// Include rmemory initializers in init blocks unless\
  \ synthesis is set\n`ifndef SYNTHESIS\n  `ifndef ENABLE_INITIAL_MEM_\n    `define\
  \ ENABLE_INITIAL_MEM_\n  `endif // not def ENABLE_INITIAL_MEM_\n`endif // not def\
  \ SYNTHESIS\n\nmodule Counter(\t// src/main/scala/Counter.scala:7:9\n  input   \
  \     clock,\t// src/main/scala/Counter.scala:7:9\n               reset,\t// src/main/scala/Counter.scala:7:9\n\
  \               io_enable,\t// src/main/scala/Counter.scala:8:16\n             \
  \  io_reset,\t// src/main/scala/Counter.scala:8:16\n  output [3:0] io_count\t//\
  \ src/main/scala/Counter.scala:8:16\n);\n\n  reg [3:0] countReg;\t// src/main/scala/Counter.scala:15:27\n\
  \  always @(posedge clock) begin\t// src/main/scala/Counter.scala:7:9\n    if (reset)\t\
  // src/main/scala/Counter.scala:7:9\n      countReg <= 4'h0;\t// src/main/scala/Counter.scala:15:27\n\
  \    else if (io_reset)\t// src/main/scala/Counter.scala:8:16\n      countReg <=\
  \ 4'h0;\t// src/main/scala/Counter.scala:15:27\n    else if (io_enable)\t// src/main/scala/Counter.scala:8:16\n\
  \      countReg <= countReg + 4'h1;\t// src/main/scala/Counter.scala:15:27, :21:28\n\
  \  end // always @(posedge)\n  `ifdef ENABLE_INITIAL_REG_\t// src/main/scala/Counter.scala:7:9\n\
  \    `ifdef FIRRTL_BEFORE_INITIAL\t// src/main/scala/Counter.scala:7:9\n      `FIRRTL_BEFORE_INITIAL\t\
  // src/main/scala/Counter.scala:7:9\n    `endif // FIRRTL_BEFORE_INITIAL\n    initial\
  \ begin\t// src/main/scala/Counter.scala:7:9\n      automatic logic [31:0] _RANDOM[0:0];\t\
  // src/main/scala/Counter.scala:7:9\n      `ifdef INIT_RANDOM_PROLOG_\t// src/main/scala/Counter.scala:7:9\n\
  \        `INIT_RANDOM_PROLOG_\t// src/main/scala/Counter.scala:7:9\n      `endif\
  \ // INIT_RANDOM_PROLOG_\n      `ifdef RANDOMIZE_REG_INIT\t// src/main/scala/Counter.scala:7:9\n\
  \        _RANDOM[/*Zero width*/ 1'b0] = `RANDOM;\t// src/main/scala/Counter.scala:7:9\n\
  \        countReg = _RANDOM[/*Zero width*/ 1'b0][3:0];\t// src/main/scala/Counter.scala:7:9,\
  \ :15:27\n      `endif // RANDOMIZE_REG_INIT\n    end // initial\n    `ifdef FIRRTL_AFTER_INITIAL\t\
  // src/main/scala/Counter.scala:7:9\n      `FIRRTL_AFTER_INITIAL\t// src/main/scala/Counter.scala:7:9\n\
  \    `endif // FIRRTL_AFTER_INITIAL\n  `endif // ENABLE_INITIAL_REG_\n  assign io_count\
  \ = countReg;\t// src/main/scala/Counter.scala:7:9, :15:27\nendmodule\n\n
"""

    # Instantiate the checker
    checker = Equiv_check()

    # Setup: checks if Yosys is accessible
    # If Yosys is not in PATH or not installed, this returns False
    ok = checker.setup()
    if not ok:
        print(f'Equiv_check setup failed: {checker.get_error()}')
        return

    # Run the equivalence check
    try:
        result = checker.check_equivalence(gold_code, ref_code)
    except Exception as e:
        print(f'Error during check_equivalence: {e}')
        return

    # Interpret the result
    if result is True:
        print('Designs are equivalent.')
    elif result is False:
        print('Designs are NOT equivalent.')
        cex = checker.get_counterexample()
        if cex:
            print(f'Counterexample: {cex}')
    else:
        # None => unknown or inconclusive
        print('Equivalence check inconclusive.')
        print(f'Error message: {checker.get_error()}')


if __name__ == '__main__':
    main()

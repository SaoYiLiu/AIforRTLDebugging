The SystemVerilog code for `coffee_machine` module generates control signals for a coffee machine. The module receives signals that determine which operations to run, how much delay to wait during key operations, and sensor information to determine any problems in its inputs. The operation starts when the `i_start` signal is asserted and no errors are reported. Besides the error signal output (`o_error`) there are five other outputs to control the coffee machine. The module operates synchronously in the rising edge of a clock (`clk`) and an asynchronous active low reset signal (`rst_async_n`) that resets its registers.

------

### Specifications

* **Module Name**: `coffee_machine`
* **Parameters**:
   * `NBW_DLY`: Defines the bit width of delay input signals.
      * Default value: 5.
      * Can be any value bigger than 2.
   * `NBW_BEANS`: Defines the bit width of the input `i_bean_sel`, which selects the type of beans.
      * Default value: 2.
      * Can be any value bigger than 1.
   * `NS_BEANS`: Defines the width of `o_bean_sel`, which controls bean selection during the process (rounded up to a power of two.)
      * Default value: 4.
      * Must be exactly 2 to the power of `NBW_BEANS`.
   * `NS_OP`: Defines the bit width `i_operation_sel`, which determines the number of possible operations.
      * Default value: 3.
      * Can't be changed.
   * `NS_SENSOR`: Defines the bit width of the sensor input signal.
      * Default value: 4.
      * Can't be changed.

### Interface signals

* **Clock** (`clk`): Synchronizes operation in its rising edge.
* **Reset** (`rst_async_n`): Active low, asynchronous reset that resets the internal registers.
* **Operation Select Signal** (`i_operation_sel`): A 3-bit signal that configures which operation to run.
* **Grind Delay Signal** (`i_grind_delay`): A `NBW_DLY`-bit signal that configures the delay of the _GRIND_ operation.
* **Heat Delay Signal** (`i_heat_delay`): A `NBW_DLY`-bit signal that configures the delay of the _HEAT_ operation.
* **Pour Delay Signal** (`i_pour_delay`): A `NBW_DLY`-bit signal that configures the delay of the _POUR_ operation.
* **Bean Select Input Signal** (`i_bean_sel`): A `NBW_BEANS`-bit signal that select which bean to use.
* **Sensor Signal** (`i_sensor`): A 4-bit signal that indicates if there is a problem with any of the things used in the machine operation.
* **Start Signal** (`i_start`): Active high signal that controls when to start the operation.
* **Error Signal** (`o_error`): Active high signal that indicates if there is an error in performing the selected operation.
* **Bean Select Output Signal** (`o_bean_sel`): A `NS_BEANS`-bit signal that selects the bean to perform the _GRIND_ and, when necessary, _POWDER_ operations.
* **Grind Beans Signal** (`o_grind_beans`): Indicates when the coffee machine should grind beans. Will be high for the given delay.
* **Powder Signal** (`o_use_powder`): Indicates when the coffee machine should pass the water through the powder. Will be high for the given delay.
* **Heat Signal** (`o_heat_water`): Indicates when the coffee machine should heat the water. Will be high for the given delay.
* **Pour Signal** (`o_pour_coffee`): Indicates when the coffee machine should pour the water. Will be high for the given delay.

### Functional Behavior

1. **Operation**
   * The operation can start if there are no errors indicated by the `o_error` signal, `i_start` is asserted, and the coffee machine is in _IDLE_ state, that is, all outputs are equal to `0`.
   * The last operation must always be _POUR_, where the signal `o_pour_coffee` is asserted.
   * During the operation, all inputs, except `i_sensor[3]`, must be ignored and the value that they were set to when `i_start` triggered an operation start must be used for this operation.

2. **State description**: All other output signals must be set to `0` in the state that they are not mentioned.
   * _IDLE_: All outputs are `0`.
   * _BEAN_SEL_: `o_bean_sel` must select the correct bean, according to the `i_bean_sel` module's input. The `i_bean_sel`-th bit of `o_bean_sel` must be `1` and all others must be `0`. An example, using default parameter values, if `i_bean_sel = 2'd3`, then `o_bean_sel = 4'b1000`.
   * _GRIND_: `o_bean_sel` must remain unchanged. `o_grind_beans` must be asserted.
   * _POWDER_: `o_use_powder` must be asserted.
   * _HEAT_: `o_heat_water` must be asserted.
   * _POUR_: `o_pour_coffee` must be asserted.

3. **Possible Operations**
   * `i_operation_sel == 3'b000`: Steps: _HEAT_ and then _POUR_.
   * `i_operation_sel == 3'b001`: Steps: _HEAT_, _POWDER_ and then _POUR_.
   * `i_operation_sel == 3'b010`: Steps: _BEAN_SEL_, _GRIND_, _HEAT_, _POWDER_ and then _POUR_.
   * `i_operation_sel == 3'b011`: Steps: _BEAN_SEL_, _GRIND_, _POWDER_ and then _POUR_.
   * `i_operation_sel == 3'b100`: Steps: _POWDER_ and then _POUR_.
   * `i_operation_sel == 3'b101`: Steps: _POUR_.
   * `i_operation_sel == 3'b110`: Not allowed. It must trigger an error.
   * `i_operation_sel == 3'b111`: Not allowed. It must trigger an error.

4. **Sensor Input**: Each bit indicates a different error, described below.
   * `i_sensor[0]`: No water available.
   * `i_sensor[1]`: No beans available.
   * `i_sensor[2]`: No powder available.
   * `i_sensor[3]`: Generic error.

5. **Error Signal**: It is asserted regardless of `i_start` signal. The operation **can't** start, regardless of `i_start`, if `o_error` is asserted. There are two times that it can be updated:
   1. When the FSM is in _IDLE_ state:
      * If `i_sensor[0] == 1` `o_error` must be asserted.
      * If `i_sensor[1] == 1` and the configured operation uses the states _BEAN_SEL_ or _GRIND_, `o_error` must be asserted.
      * If `i_sensor[2] == 1` and the configured operation uses the state _POWDER_ which **does not** need beans, `o_error` must be asserted.
      * If `i_operation_sel == 3'b110 or i_operation_sel == 3'b111`, `o_error` must be asserted.
   2. Whatever state the FSM is in:
      * If `i_sensor[3] == 1`, `o_error` must be asserted and the state **must** change to _IDLE_. . This is the only error that can happen in the middle of an operation and must return the FSM to _IDLE_, all other errors must not reset the operation.

6. **Delays**: The states _BEAN_SEL_ and _POWDER_ must have a fixed delay of `3` and `2` cycles, respectively. The delays described in the **Interface Signals** must be applied in their described states.

## Observed Behavior

In all examples below, the delays were set to:
* `i_grind_delay = 4`
* `i_heat_delay = 3`
* `i_pour_delay = 2`
* `i_bean_sel = 1`

They remained unchanged during the operation. To start the operation, after setting the `i_operation_sel` signal to the ones described in the table below, `i_start` was asserted in a single pulse to start the operation and then was set to `0`.

The number of cycles was calculated by observing the first rising edge of `clk` that `i_start` is asserted, and the first rising edge of `clk` that all output signals are set to `0`.

| Operation | Sensor |          Observed Operations          |          Expected Operations          | Observed Cycles | Expected Cycles | Observed Error | Expected Error |
|:---------:|:------:|:-------------------------------------:|:-------------------------------------:|:---------------:|:---------------:|----------------|----------------|
|   3'b000  |  4'h0  |                  NONE                 |              _HEAT, POUR_             |   Unavailable   |        7        | NO             | NO             |
|   3'b001  |  4'h0  |                  NONE                 |          _HEAT, POWDER, POUR_         |   Unavailable   |        9        | NO             | NO             |
|   3'b010  |  4'h0  | _BEAN_SEL, GRIND, HEAT, POWDER, POUR_ | _BEAN_SEL, GRIND, HEAT, POWDER, POUR_ |        18       |        16       | NO             | NO             |
|   3'b011  |  4'h0  |    _BEAN_SEL, GRIND, POWDER, POUR_    |    _BEAN_SEL, GRIND, POWDER, POUR_    |        14       |        13       | NO             | NO             |
|   3'b100  |  4'h0  |             _POWDER, POUR_            |             _POWDER, POUR_            |        5        |        6        | NO             | NO             |
|   3'b101  |  4'h0  |                 _POUR_                |                 _POUR_                |        5        |        4        | NO             | NO             |
|   3'b110  |  4'h0  | _BEAN_SEL, GRIND, HEAT, POWDER, POUR_ |                  NONE                 |        18       |   Unavailable   | YES            | YES            |
|   3'b111  |  4'h0  |    _BEAN_SEL, GRIND, POWDER, POUR_    |                  NONE                 |        14       |   Unavailable   | YES            | YES            |
|   3'b000  |  4'h8  |                  NONE                 |                  NONE                 |   Unavailable   |   Unavailable   | YES            | YES            |
|   3'b001  |  4'h1  |                  NONE                 |                  NONE                 |   Unavailable   |   Unavailable   | YES            | YES            |
|   3'b010  |  4'h2  |                  NONE                 |                  NONE                 |   Unavailable   |   Unavailable   | YES            | YES            |
|   3'b100  |  4'h4  |                  NONE                 |                  NONE                 |   Unavailable   |   Unavailable   | YES            | YES            |

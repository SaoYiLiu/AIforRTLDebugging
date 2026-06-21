A **mux_sync** is a digital circuit used to synchronize a data path between two asynchronous clock domains. To synchronize the data, a control pulse is generated in the source clock domain when data becomes available at the source flop. This control pulse is then synchronized using a two-flip-flop synchronizer. The synchronized control pulse is used to sample the data on the bus in the destination domain. The data must remain stable until it is sampled in the destination clock domain. and once the data is sampled in the destination domain a acknowledgment signal which transmitted back to source domain through a 2 flop synchronizer.


During testing it is found that sometime the acknowledgment signal `ack_out` is not  reaching back to the destination clock domain.

**Bug Description:**
   - In the provided RTL,  when data is crossing from the slower to the faster clock domain, the acknowledgment signal will cross from the faster to the slower clock domain, that means whenever the `ack_out` pulse occurs in such a way that the pulse happens in between the 2 active edge of source clock (in our case positive edge) the synchronizer will not sample it.
   - but whenever the `ack_out` pulse occurs in such a way that the pulse happens to overlap an active edge of source clock (in our case positive edge) the synchronizer will sample it.
   -  the first scenarios is bug and it should be fixed

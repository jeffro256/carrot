# Carrot

Carrot (Cryptonote Address on Rerandomizable-RingCT-Output Transactions) is an addressing protocol for the upcoming FCMP++ upgrade to Monero which maintains backwards compatibility with existing addresses. It does this while bringing new privacy and usability features, such as outgoing view keys. Carrot is not the only upcoming addressing protocol for Monero's FCMP++ consensus protocol. The other big contender is Jamtis, for which Carrot is designed to be indistinguishable on-chain, which will justify some seemingly strange design choices later on in this document. 

## Background

### Cryptonote Addresses, Integrated Addresses, and Subaddresses

In 2013, the Cryptonote whitepaper [[citation](https://github.com/monero-project/research-lab/blob/master/whitepaper/whitepaper.pdf)] introduced an addressing scheme which remains a crucial component of Monero's privacy model today, providing recipient unlinkability across transactions. Unlike Bitcoin, which uses transparent addresses, Monero's use of addresses ensures that all created transaction outputs cannot be attributed to any single receiver regardless of the number of times an address is reused, and without requiring interactivity.

In the beginning, since there was only one address per wallet, a method was needed for receivers to differentiate their senders. *Payment IDs* [[citation](https://www.getmonero.org/resources/moneropedia/paymentid.html)], an arbitrary 32 byte string attached to transactions, was the initial solution to this problem. The aim was that users sending funds would include a 32 byte message that gave the recipient user enough evidence to attribute that transaction to them. *Integrated addresses* improved the UX of these payment IDs by having the recipient's wallet generate and include them inside of addresses, which were automatically added to the transaction data by the sender's wallet. They were also shortened to 8 bytes. Wallets then started encrypting the payment IDs on-chain, and adding dummies if no payment IDs were used, which greatly improved privacy.

In 2016, Monero iterated even further by introducing *subaddresses* [[citation](https://github.com/monero-project/research-lab/issues/7)], an addressing scheme that existing wallets could adopt, allowing them to generate an arbitrary number of unlinkable receiving addresses without affecting scan speed.

### FCMP++

To tackle privacy shortcomings with ring signatures, there is a consensus protocol update planned for Monero called FCMP++, which allows for an "anonymity set" of the entire chain. This protocol leverages a primitive for set membership called *Curve Trees*. Curve Trees allows one to efficiently prove that a "rerandomized" curve point exists in some set without revealing the element. In Monero, this set is defined as all "spendable" (i.e. unlocked and valid) transaction outputs on-chain. This randomization transformation is similar to "blinding" coin amounts in Pederson Commitments, and as a side effect, transaction output public keys *themselves* can be rerandomized on-chain. This fact opens the door for addressing protocols to add long-desired features, namely forward secrecy and outgoing view keys.

## New Features

### Address generator

This tier is intended for merchant point-of-sale terminals. It can generate addresses on demand, but otherwise has no access to the wallet (i.e. it cannot recognize any payments in the blockchain).

### Payment validator wallets

Carrot supports view-incoming-only wallets that can verify that an external payment was received into the wallet, without the ability to see where those payment enotes were spent, or spend it themselves. But unlike old Monero view-only wallets, a Carrot payment validator wallet cannot see *"internal"* change enotes.

### Full view-only wallets

Carrot supports full view-only wallets that can identify spent outputs (unlike legacy view-only wallets), so they can display the correct wallet balance and list all incoming and outgoing transactions.

### Janus attack mitigation

A Janus attack [[citation](https://web.getmonero.org/2019/10/18/subaddress-janus.html)] is a targeted attack that aims to determine if two addresses A, B belong to the same wallet. Janus outputs are crafted in such a way that they appear to the recipient as being received to the wallet address B, while secretly using a key from address A. If the recipient confirms the receipt of the payment, the sender learns that they own both addresses A and B.

Carrot prevents this attack by allowing the recipient to recognize a Janus output.

### Stateless burning bug mitigation

The burning bug [[citation](https://www.getmonero.org/2018/09/25/a-post-mortum-of-the-burning-bug.html)] is a undesirable result of Monero's old scan process wherein if an exploiter creates a transaction with the same ephemeral pubkey, output pubkey, and transaction output index as an existing transaction, a recipient will scan both instances of these enotes as "owned" and interpret their balance as increasing. However, since key images are linked to output pubkeys, the receiver can only spend one of these enotes, "burning" the other. If the exploiter creates an enote with amount `a = 0`, and the receiver happens to spend that enote first, then the receiver burns all of the funds in their original enote with only a tiny fee cost to the exploiter!

An initial patch [[citation](https://github.com/monero-project/monero/pull/4438/files#diff-04cf14f64d2023c7f9cd7bd8e51dcb32ed400443c6a67535cb0105cfa2b62c3c)] was introduced secretly to catch when such an attempted attack occurred. However, this patch did not attempt to recover gracefully and instead simply stopped the wallet process with an error message. Further iterations of handling this bug automatically discarded all instances of duplicate output pubkeys which didn't have the greatest amount. However, all instances of burning bug handling in Monero Core require a complete view of all scanning history up to the current chain tip, which makes the workarounds somewhat fragile.

The original Jamtis [[citation](https://gist.github.com/tevador/50160d160d24cfc6c52ae02eb3d17024)] proposal by @tevador and the *Guaranteed Address* [[citation](https://gist.github.com/kayabaNerve/8066c13f1fe1573286ba7a2fd79f6100)] proposal by @kayabaNerve were some of the first examples of addressing schemes where attempting a burn in this manner is inherently computationally intractable. These schemes somehow bind the output pubkey to an "input context" value, which is unique for every transaction. Thus, the receiver will only ever correctly determine an enote with a given output pubkey to be spendable for a single transaction, avoiding the burning bug without ever having to maintain a complete scan state.

Carrot prevents this attack statelessly in the same manner.

### Address-conditional forward secrecy

As a result of leveraging the FCMP++ consensus protocol, Carrot has the ability to hide all transaction details (sender, receiver, amount) from third-parties with the ability to break the security of elliptic curves (e.g. quantum computers), as long as the observer does not know receiver's addresses.

### Internal forward secrecy

Enotes that are sent "internally" to one's own wallet will have all transactions details hidden (sender, receiver, amount) from third-parties with the ability to break the security of elliptic curves (e.g. quantum computers), even if the observer has knowledge of the receiver's addresses.

### Payment ID confirmation

Payment IDs are confirmed by a cryptographic hash, which gives integrated address payment processors better guarantees, provides better UX, and allows many-output batched transactions to unambiguously include an integrated address destination.

## Notation

### Miscellaneous definitions

1. The function `BytesToInt256(x)` deserializes a 256-bit little-endian integer from a 32-byte input.
1. The function `BytesToInt512(x)` deserializes a 512-bit little-endian integer from a 64-byte input.
1. The function `IntToBytes32(x)` serializes an integer into a little-endian encoded 4-byte output.
1. The function `IntToBytes64(x)` serializes an integer into a little-endian encoded 8-byte output.
1. The function `IntToBytes256(x)` serializes an integer into a little-endian encoded 32-byte output.
1. The function `RandBytes(x)` generates a random x-byte string.
1. Concatenation is denoted by `||`.
1. Bit-wise XOR (exclusive-or) is denoted by `⊕`.

### Hash functions

The function <code>H<sub>b</sub>(x)</code> with parameters `b, x`, refers to the Blake2b hash function [[citation](https://eprint.iacr.org/2013/322.pdf)] initialized as follows:

* The output length is set to `b` bytes.
* Hashing is done in sequential mode.
* The Personalization string is set to the ASCII value "Monero", padded with zero bytes.
* The input `x` is hashed.

The function `SecretDerive` is defined as:

<code>SecretDerive(x) = H<sub>32</sub>(x)</code>

The function `Keccak256(x)` refers to the Keccak function [[citation](https://keccak.team/keccak.html)] parameterized with `r = 1088, c = 512, d = 256`.

### Elliptic curves

Two elliptic curves are used in this specification:

1. **Curve25519** - a Montgomery curve. Points on this curve include a cyclic subgroup 𝔾<sub>M</sub>.
1. **Ed25519** - a twisted Edwards curve. Points on this curve include a cyclic subgroup 𝔾<sub>E</sub>.

Both curves are birationally equivalent, so the subgroups 𝔾<sub>M</sub> and 𝔾<sub>E</sub> have the same prime order <code>ℓ = 2<sup>252</sup> + 27742317777372353535851937790883648493</code>. The total number of points on each curve is `8ℓ`.

#### Curve25519

The Montgomery curve Curve25519 [[citation](https://cr.yp.to/ecdh/curve25519-20060209.pdf)] is used exclusively for the Diffie-Hellman key exchange with the private incoming view key. Only a single generator point `B`, where `x = 9`, is used.

Elements of 𝔾<sub>M</sub> are denoted by `D`, and are serialized as their x-coordinate. Scalar multiplication is denoted by a space, e.g. <code>D = d B</code>. In this specification, we always perform a "full" scalar multiplication on Curve25519 without scalar clamping, a notable difference from typical X25519 implementations. Using a clamped scalar multiplication will break completeness of the ECDH for existing pubkeys in addresses for which the private keys can be any element of **F**<sub>*ℓ*</sub>.

#### Ed25519

The twisted Edwards curve Ed25519 [[citation](https://ed25519.cr.yp.to/ed25519-20110926.pdf)] is used for all other cryptographic operations on FCMP++. The following generators are used:

|Point|Derivation|Serialized (hex)|
|-----|----------|----------|
| `G` | generator of 𝔾<sub>E</sub> | `5866666666666666666666666666666666666666666666666666666666666666`
| `H` | <code>H<sub>p</sub><sup>1</sup>(G)</code> | `8b655970153799af2aeadc9ff1add0ea6c7251d54154cfa92c173a0dd39c1f94`
| `T` | <code>H<sub>p</sub><sup>2</sup>(Keccak256("Monero generator T"))</code> | `966fc66b82cd56cf85eaec801c42845f5f408878d1561e00d3d7ded2794d094f`

Here <code>H<sub>p</sub><sup>1</sup></code> and <code>H<sub>p</sub><sup>2</sup></code> refer to two hash-to-point functions on Ed25519.

Elements of 𝔾<sub>E</sub> are denoted by `K` or `C` and are serialized as 256-bit integers, with the lower 255 bits being the y-coordinate of the corresponding Ed25519 point and the most significant bit being the parity of the x-coordinate. Scalar multiplication is denoted by a space, e.g. <code>K = k G</code>.

#### Point conversion

We define a function `ConvertPubkeyE(K)` that can transform an Ed25519 curve point into a Curve25519 point, preserving group structure. The conversion is done with the equivalence `x = (v + 1) / (1 - v)`, where `v` is the Ed25519 y-coordinate and `x` is the Curve25519 x-coordinate. Notice that the x-coordinates of Ed25519 points and the y-coordinates of Curve25519 points are not considered. Since the y coordinate is ignored during serialization of Curve25519 points, the conversion should be unambiguous, with only one result.

#### Private keys

Private keys for both curves are elements of the field **F**<sub>*ℓ*</sub>. These keys are not "clamped" [[citation](https://neilmadden.blog/2020/05/28/whats-the-curve25519-clamping-all-about/)] like they would be in the X25519 [[citation](https://cr.yp.to/ecdh.html)] protocol. Unfortunately, this somewhat slows down implementations of Curve25519 scalar-point multiplications, but it must be this way for backwards compatibility and on-chain indistinguishability. Private keys are derived using one of the two following functions:

1. <code>ScalarDerive(x) = BytesToInt512(H<sub>64</sub>(x)) mod ℓ</code>
1. <code>ScalarDeriveLegacy(x) = BytesToInt256(Keccak256(x)) mod ℓ</code>

## Rerandomizable RingCT abstraction

Here we formally define an abstraction of the FCMP++ consensus layer called *Rerandomizable RingCT* which lays out the requirements that Carrot needs. All elliptic curve arithmetic occurs on Ed25519.

### Creating a transaction output

Transaction outputs are defined as the two points <code>(K<sub>o</sub>, C<sub>a</sub>)</code>. To create a valid transaction output, the sender must know `z, a` such that <code>C<sub>a</sub> = z G + a H</code> where <code>0 ≤ a < 2<sup>64</sup></code>. Coinbase transactions have a plaintext integer amount `a` instead of the amount commitment <code>C<sub>a</sub></code>, which is implied to be <code>C<sub>a</sub> = G + a H</code>.

### Spending a transaction output

To spend this output, the recipient must know `x, y, z, a` such that <code>K<sub>o</sub> = x G + y T</code> and <code>C<sub>a</sub> = z G + a H</code> where <code>0 ≤ a < 2<sup>64</sup></code>. Spending an output necessarily emits a *key image* (AKA *"linking tag"* or *"nullifier"*) <code>L = x H<sub>p</sub><sup>2</sup>(K<sub>o</sub>)</code>. All key images must be in the prime order subgroup 𝔾<sub>E</sub>.

### Transaction model

Transactions contain a list of outputs, a list of key images, and additional unstructured data. All key images must be unique within a transaction. In non-coinbase transactions, the list of transaction outputs must be sorted according to a total partial order [[citation](https://en.wikipedia.org/wiki/Total_order)] 𝑹<sub>ac</sub> on the amount commitments of the outputs.

𝑹<sub>ac</sub> will typically be defined as the lexicographical "less-than-or-equal" comparison on the bytes of the serialized amount commitment, but the precise definition is not critical as long as it is partial and total. This rule is in place to prevent accidental fingerprinting of output order by forcing senders to order outputs by the result of a one-way function (elliptic curve scalar-point multiplication). Encoding explicit order information into a valid finalized transaction would require the sender to "mine" blinding factors on the amount commitments. Contrast this to the pre-FCMP Monero consensus protocol which does not enforce any order to transaction outputs. Transaction construction code in the reference codebase calls a in-place shuffling function [[citation](https://github.com/monero-project/monero/blob/a1dc85c5373a30f14aaf7dcfdd95f5a7375d3623/src/cryptonote_core/cryptonote_tx_utils.cpp#L358)] on the user-provided destinations to obfuscate information about the intention of destinations as well as miscellaneous implementation details. However, a less diligent wallet developer might forget to include this step, damaging their users' privacy.

Note that since 𝑹<sub>ac</sub> is partial, duplicate amount commitments within a single transaction are allowed, even though "honest" Carrot senders will never construct the same amount commitment twice. The reason for this design choice over a strict ordering is that disallowing duplicates would allow a "copy-cat" counterparty to perform denial-of-service attacks in collaborative transaction construction protocols. One may also wonder why this order is enforced on the amount commitments instead of the output pubkeys. Not ordering on the output pubkeys allows addressing protocols, like Carrot, to bind the output pubkey to its index within the output list, providing more robust protection against burning bug attacks.

### Ledger model

The ledger can be modeled as an append-only list of transactions. Transactions can only contain key images of transaction outputs of "lower" positions within the ledger list. No two key images in any transaction in the ledger are ever equal to each other. In practice, the ledger will contain additional cryptographic proofs that verify the integrity of the data within each transaction, but those can largely be ignored for this addressing protocol.

## Wallets

### Legacy key hierarchy

The following figure shows the overall hierarchy used for legacy wallet keys. Note that the private spend key <code>k<sub>s</sub></code> doesn't exist for multi-signature wallets.

```
k_s (spend key)
 |
 |
 |
 +- k_v (view key)
```

| Key                       | Name      | Derivation                                                     | Used to |
|---------------------------|-----------|----------------------------------------------------------------|---------|
|<code>k<sub>s</sub></code> | spend key | random element of **F**<sub>*ℓ*</sub>                          | calculate key images, spend enotes |
|<code>k<sub>v</sub></code> | view key  | <code>k<sub>v</sub> = ScalarDeriveLegacy(k<sub>s</sub>)</code> | find and decode received enotes, generate addresses |

### New key hierarchy

The following figure shows the overall hierarchy one should use for new wallet keys. Users do not *have* to switch their key hierarchy in order to participate in the address protocol, but this hierarchy gives the best features and usability. Note that the master secret <code>s<sub>m</sub></code> doesn't exist for multi-signature wallets.

```
s_m (master secret)
 |
 |
 |
 +- k_ps (prove-spend key)
 |
 |
 |
 +- s_vb (view-balance secret)
     |
     |
     |
     +- k_gi (generate-image key)
     |
     |
     |
     +- k_v (incoming view key)
     |
     |
     |
     +- s_ga (generate-address secret)
```

| Key | Name | Derivation | Used to |
|-----|------|------------|-------|
|<code>k<sub>ps</sub></code> | prove-spend key         | <code>k<sub>ps</sub> = ScalarDerive("jamtis_prove_spend_key" \|\| s<sub>m</sub>)</code>                  | spend enotes |
|<code>s<sub>vb</sub></code> | view-balance secret     | <code>s<sub>vb</sub> = SecretDerive("jamtis_view_balance_secret" \|\| s<sub>m</sub>)</code>              | find and decode received and outgoing enotes |
|<code>k<sub>gi</sub></code> | generate-image key      | <code>k<sub>gi</sub> = ScalarDerive("jamtis_generate_image_key" \|\| s<sub>vb</sub>)</code>              | generate key images |
|<code>k<sub>v</sub></code>  | incoming view key       | <code>k<sub>v</sub> = ScalarDerive("carrot_view_key" \|\| s<sub>vb</sub>)</code>                         | find and decode received enotes |
|<code>s<sub>ga</sub></code> | generate-address secret | <code>s<sub>ga</sub> = SecretDerive</sub>("jamtis_generate_address_secret" \|\| s<sub>vb</sub>)</code> | generate addresses |

### New wallet public keys

There are two global wallet public keys for the new private key hierarchy.

| Key | Name | Value |
|-----|------|-------|
|<code>K<sub>s</sub></code> | spend key    | <code>K<sub>s</sub> = k<sub>gi</sub> G + k<sub>ps</sub> T</code></code> |
|<code>K<sub>v</sub></code> | view key     | <code>K<sub>v</sub> = k<sub>v</sub> K<sub>s</sub></code>                |

Note: for legacy key hierarchies, <code>K<sub>s</sub> = k<sub>s</sub> G</code>.

### New wallet access tiers

The new private key hierarchy enables the following useful wallet tiers:

| Tier             | Secret                      | Off-chain capabilities    | On-chain capabilities |
|------------------|-----------------------------|---------------------------|-----------------------|
| Generate-Address | <code>s<sub>ga</sub></code> | generate public addresses | none                  |
| View-Received    | <code>k<sub>v</sub>         | all                       | view received         |
| View-All         | <code>s<sub>vb</sub></code> | all                       | view all              |
| Master           | <code>s<sub>m</sub></code>  | all                       | all                   |

#### Generate-Address

This wallet tier can generate public addresses for the wallet. It doesn't provide any blockchain access.

#### View-Received

This tier provides the wallet with the ability to see all external payments and external change, but cannot see any internal enotes, nor where any enotes are spent.

#### View-All

This is a full view-only wallet than can see all external and internal payment and change enotes, as well as where they are spent (and thus can calculate the correct wallet balance).

#### Master wallet (Master)

This tier has full control of the wallet.

## Addresses

### Address generation

There are two cryptographically distinct address types in Monero: Cryptonote and subaddress. Note that integrated addresses are derived exactly like a Cryptonote address, but they have an additional payment ID included. There can only be a maximum of one Cryptonote address per view key, referred to as the *main* address, but any number of subaddresses.

By convention, subaddresses are generated from a "subaddress index", which is a tuple of two 32-bit unsigned integers <code>(j<sub>major</sub>, j<sub>minor</sub>)</code>, which allows for 2<sup>64</sup> addresses. The reason for the distinction between <code>j<sub>major</sub></code> and <code>j<sub>minor</sub></code> is simply for UX reasons. The "major" index is used to make separate "accounts" per wallet, which is used to compartmentalize input selection, change outputs, etc. The subaddress index `(0, 0)` is used to designate the main address, even though the key derivation is different. For brevity's sake, we use the label `j` as shorthand for <code>(j<sub>major</sub>, j<sub>minor</sub>)</code> and `0` as a shorthand for `(0, 0)`.

Each Monero address derived from index `j` transmits information <code>(is_main, K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>, pid)</code>, where `is_main` is a boolean flag which is `true` for Cryptonote addresses, and `false` for subaddresses.

#### Main address keys

The two public keys of the main address are constructed as:

* <code>K<sub>s</sub><sup>0</sup> = K<sub>s</sub></code>
* <code>K<sub>v</sub><sup>0</sup> = k<sub>v</sub> G</code>

#### Subaddress keys (Legacy Hierarchy)

Under the legacy key hierarchy, the two public keys of the subaddress at index `j` are constructed as:

* <code>k<sub>sub_ext</sub><sup>j</sup> = ScalarDeriveLegacy(IntToBytes64(8) \|\| k<sub>v</sub> \|\| IntToBytes32(j<sub>major</sub>) \|\| IntToBytes32(j<sub>minor</sub>))</code>
* <code>K<sub>s</sub><sup>j</sup> = K<sub>s</sub> + k<sub>sub_ext</sub><sup>j</sup> G</code>
* <code>K<sub>v</sub><sup>j</sup> = k<sub>v</sub> K<sub>s</sub><sup>j</sup></code>

Notice that generating new subaddresses this way requires knowledge of <code>k<sub>v</sub></code> which necessarily ties the ability to generate subaddresses to the ability to find owned enotes.

#### Subaddress keys (New Hierarchy)

Under the new key hierarchy, the two public keys of the subaddress at index `j` are constructed as:

* <code>s<sub>gen</sub><sup>j</sup> = SecretDerive("jamtis_address_index_generator" \|\| s<sub>ga</sub> \|\| IntToBytes32(j<sub>major</sub>) \|\| IntToBytes32(j<sub>minor</sub>))</code>
* <code>k<sub>a</sub><sup>j</sup> = ScalarDerive("carrot_subaddress_scalar" \|\| s<sub>gen</sub><sup>j</sup> \|\| K<sub>s</sub> \|\| K<sub>v</sub> \|\| IntToBytes32(j<sub>major</sub>) \|\| IntToBytes32(j<sub>minor</sub>))</code>
* <code>K<sub>s</sub><sup>j</sup> = k<sub>a</sub><sup>j</sup> K<sub>s</sub></code>
* <code>K<sub>v</sub><sup>j</sup> = k<sub>a</sub><sup>j</sup> K<sub>v</sub></code>

The address index generator <code>s<sub>gen</sub><sup>j</sup></code> can be used to prove that the address was constructed from the index `j` and the public keys <code>K<sub>s</sub></code> and <code>K<sub>v</sub></code> without revealing <code>s<sub>ga</sub></code>. Notice that, unlike the legacy derivation, the new subaddress derivation method does not require the private incoming view key <code>k<sub>v</sub></code>, only the generate-address secret <code>s<sub>ga</sub></code>, which allows for private deferred address generation.

## Addressing protocol

### Transaction global fields

#### Payment ID

A single 8-byte encrypted payment ID field is included in non-coinbase transactions for backwards compatibility with integrated addresses. Because only one encrypted payment ID <code>pid<sub>enc</sub></code> is included per transaction, senders can only send to one integrated addresses per transaction. When not sending to a legacy integrated address, `pid` is set to `nullpid`, the payment ID of all zero bytes.

The payment ID `pid` is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>pid</sub></code>. The encryption mask is derived from the shared secrets of the payment enote.

#### Ephemeral public keys

Every 2-output transaction has one ephemeral public key <code>D<sub>e</sub></code>. Transactions with `N > 2` outputs have `N` ephemeral public keys (one for each output). Coinbase transactions always have one key per output.

### Input Context

For each transaction, we assign a value `input_context`, whose purpose is to be unique for every single transaction within a valid ledger. We define this value as follows:

| transaction type | `input_context`                                   |
|----------------- |-------------------------------------------------- |
| coinbase         | <code>"C" \|\| IntToBytes256(block height)</code> |
| non-coinbase     | <code>"R" \|\| first spent key image</code>       |

This uniqueness is guaranteed by consensus rules: there is exactly one coinbase transaction per block height, and all key images are unique. Indirectly binding output pubkeys to this value helps to mitigate burning bugs.

### Enote format

Each enote represents an amount `a` and payment ID `pid` sent to an address <code>(is_main, K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>)</code>.

An enote contains the output public key <code>K<sub>o</sub></code>, the 3-byte view tag `vt`, the amount commitment <code>C<sub>a</sub></code>, encrypted Janus anchor <code>anchor<sub>enc</sub></code>, and encrypted amount <code>a<sub>enc</sub></code>. For coinbase transactions, the amount commitment <code>C<sub>a</sub></code> is omitted and the amount is not encrypted.

#### The output pubkey

The output pubkey, sometimes referred to as the "one-time address", is a part of the underlying Rerandomizable RingCT transaction output. Knowledge of the opening of this point allows for spending of the enote. Partial opening knowledge allows for calculating the key image of this enote, signalling in which location it was spent.

#### Amount commitment

The amount commitment is also part of the underlying Rerandomizable RingCT transaction output. This Pederson commitment should open up to the decrypted value in <code>a<sub>enc</sub></code> and the blinding factor derived from the shared secret. Coinbase transactions have this field omitted.

#### Amount

In non-coinbase transactions, the amount `a` is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>a</sub></code>. In coinbase transactions, `a` is included as part of the enote in plaintext.

#### View tags

The view tag `vt` is the first 3 bytes of a hash of the ECDH exchange with the view key. This view tag is used to fail quickly in the scan process for enotes not intended for the current wallet. The bit size of 24 was chosen as the fixed size because of Jamtis requirements.

#### Janus anchor

The Janus anchor `anchor` is a 16-byte encrypted array that provides protection against Janus attacks in Carrot. The anchor is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>anchor</sub></code>. In the case of normal transfers, <code>anchor</code> is uniformly random, and used to re-derive the enote ephemeral private key <code>d<sub>e</sub></code> and check the enote ephemeral pubkey <code>D<sub>e</sub></code>. In *special* enotes, <code>anchor</code> is set to a HMAC of <code>D<sub>e</sub></code>, authenticated by the private view key <code>k<sub>v</sub></code>. Both of these derivation-and-check paths should only pass if either A) the sender constructed the enotes in a way which does not allow for a Janus attack or B) the sender knows the private view key, in which case they can determine that addresses belong to a wallet without performing a Janus attack.

### Pre-sort derivations

In the pre-sort stage, we define how to derive the ephemeral private and public keys, the (uncontextualized) sender-receiver shared secret, and the amount commitment for an enote. For senders, this stage of the addressing protocol must be done for all enotes in a transaction before they can move onto the next stage for any single enote. This is because the enote components derived in the post-sort stage are bound to the index of the output within the transaction, which itself depends on the value of the amount commitment.

#### Ephemeral private key

| Symbol                           | Name                | Derivation                                         |
|----------------------------------|---------------------|----------------------------------------------------|
|<code>anchor<sub>norm</sub></code>|janus anchor, normal | <code>anchor<sub>norm</sub> = RandBytes(16)</code> |
|<code>d<sub>e</sub></code>        |ephemeral private key| <code>d<sub>e</sub> = ScalarDerive("carrot_sending_key_normal" \|\| anchor<sub>norm</sub> \|\| input_context \|\| K<sub>s</sub><sup>j</sup> \|\| K<sub>v</sub><sup>j</sup> \|\| pid)</code> |

#### Ephemeral public key

The ephemeral pubkey <code>D<sub>e</sub></code>, a Curve25519 point, for a given enote is constructed differently based on what type of address one is sending to, how many outputs are in the transaction, and whether we are deriving on the internal or external path. Here "special" means an *external self-send* enote in
a 2-out transaction. "Normal" refers to non-special, non-internal enotes.

| Transfer Type            | <code>D<sub>e</sub></code> Derivation                                |
|--------------------------|----------------------------------------------------------------------|   
| Normal, to main address  | <code>d<sub>e</sub> B</code>                                         |
| Normal, to subaddress    | <code>d<sub>e</sub> ConvertPubkeyE(K<sub>s</sub><sup>j</sup>)</code> |
| Internal                 | random element of 𝔾<sub>M</sub>                                      |
| Special                  | <code>D<sub>e</sub><sup>other</sup></code>                           |

<code>D<sub>e</sub><sup>other</sup></code> refers to the ephemeral pubkey that would be derived on the *other* enote in a 2-out transaction. If both enotes in a 2-out transaction are "special", then no specific derivation of <code>D<sub>e</sub></code> is required, and <code>D<sub>e</sub></code> should be set to a random element of 𝔾<sub>M</sub>.

#### Sender-receiver shared secret

The shared secret <code>s<sub>sr</sub></code> is used indirectly to encrypt/extend all components of Carrot transactions. It is derived in one of the following ways:

|                          | Derivation                                                            |
|------------------------- | ----------------------------------------------------------------------|
|Sender, external, normal  |<code>8 d<sub>e</sub> ConvertPubkeyE(K<sub>v</sub><sup>j</sup></code>) |
|Sender, external, special |<code>8 k<sub>v</sub> D<sub>e</sub></code>                             |
|Recipient, external       |<code>8 k<sub>v</sub> D<sub>e</sub></code>                             |
|Internal                  |<code>s<sub>vb</sub></code>                                            |

#### Amount commitment

| Symbol                           | Name                            | Derivation                              |
|----------------------------------|---------------------------------|-----------------------------------------|
|<code>k<sub>a</sub></code>        |amount commitment blinding factor| <code>k<sub>a</sub> = ScalarDerive("jamtis_commitment_mask" \|\| s<sub>sr</sub> \|\| input_context \|\| enote_type)</code>                       |
|<code>C<sub>a</sub></code>        |amount commitment                | <code>C<sub>a</sub> = k<sub>a</sub> G + a H</code>                                                                                                          |

The variable `enote_type` is `"payment"` or `"change"` depending on the sender's intended interpretation of the payment in human terms, or sometimes out of necessity.

A note for implementors: unless you intend for your transaction construction code to support collaborative protocols where multiple, potentially untrusted participants propose their own outputs, then you should assert that all amount commitment blinding factors <code>k<sub>a</sub></code> are unique. This will prevent amount commitments from being accidentally trivially related.

### Enote sorting

After <code>C<sub>a</sub></code> is known for all enotes in the transaction, the enotes can be sorted by relation 𝑹<sub>ac</sub>. Ordering of enotes with duplicate amount commitments is left open to each transaction sender. Once the enotes are sorted, they are assigned an `output_index` value, which is a 0-based integer index determined by the enotes place in the transaction's output list. Later, recipients can determine `output_index` by simply observing the index of an enote in the published transaction. Together, the values `output_index` and `input_context` are guaranteed to always be unique as a pair for every single enote on a ledger. For brevity's sake, we combine both of these values into a nonce that is used to sow uniqueness into hashes:

`enote_nonce = input_context || IntToBytes32(output_index)`

### Post-sort derivations

#### Intermediate values

| Symbol                                  | Name                                | Derivation |
|-----------------------------------------|-------------------------------------|------------|
|<code>s<sub>sr</sub><sup>ctx</sup></code>|contextualized sender-receiver secret| <code>SecretDerive("carrot_shared_secret_ctx" \|\| s<sub>sr</sub> \|\| enote_nonce)</code> |
|<code>m<sub>anchor</sub></code>          |encryption mask for `anchor`         | <code>m<sub>anchor</sub> = SecretDerive("jamtis_encryption_mask_j'" \|\| s<sub>sr</sub><sup>ctx</sup>)</code> |
|<code>m<sub>a</sub></code>               |encryption mask for `a`              | <code>m<sub>a</sub> = SecretDerive("jamtis_encryption_mask_a" \|\| s<sub>sr</sub><sup>ctx</sup>)</code> |
|<code>m<sub>pid</sub></code>             |encryption mask for `pid`            | <code>m<sub>pid</sub> = SecretDerive("jamtis_encryption_mask_pid" \|\| s<sub>sr</sub><sup>ctx</sup>)</code> |
|<code>k<sub>g</sub><sup>o</sup></code>   |output pubkey extension G            | <code>k<sub>g</sub><sup>o</sup> = ScalarDerive("jamtis_key_extension_g" \|\| s<sub>sr</sub><sup>ctx</sup>)</code> |
|<code>k<sub>t</sub><sup>o</sup></code>   |output pubkey extension T            | <code>k<sub>t</sub><sup>o</sup> = ScalarDerive("jamtis_key_extension_t" \|\| s<sub>sr</sub><sup>ctx</sup>)</code> |
|<code>anchor<sub>sp</sub></code>         |janus anchor, special                | <code>anchor<sub>sp</sub> = SecretDerive("carrot_janus_anchor_special" \|\| D<sub>e</sub> \|\| enote_nonce \|\| k<sub>v</sub> \|\| K<sub>s</sub>)</code> |

#### Transaction components

| Symbol                           | Name                  | Derivation |
|----------------------------------|-----------------------|------------|
|<code>K<sub>o</sub></code>        | output pubkey         | <code>K<sub>o</sub> = K<sub>s</sub><sup>j</sup> + k<sub>g</sub><sup>o</sup> G + k<sub>t</sub><sup>o</sup> T</code> |
|<code>a<sub>enc</sub></code>      | encrypted amount      | <code>a<sub>enc</sub> = a ⊕ m<sub>a</sub></code>   |
|`vt`                              |view tag               | <code>vt = SecretDerive("jamtis_secondary_view_tag" \|\| s<sub>sr</sub> \|\| enote_nonce)</code> |
|<code>anchor<sub>enc</sub></code> |encrypted Janus anchor | <code>anchor<sub>enc</sub> = (anchor<sub>sp</sub> if <i>special enote</i>, else anchor<sub>norm</sub>) ⊕ m<sub>anchor</sub></code> |
|<code>pid<sub>enc</sub></code>    |encrypted payment ID   | <code>pid<sub>enc</sub> = pid ⊕ m<sub>pid</sub></code> |

### Janus outputs

In case of a Janus attack, the recipient will derive different values of the enote ephemeral pubkey <code>D<sub>e</sub></code> and Janus `anchor`, and thus will not recognize the output.

### Self-send enotes

Self-send enotes are any enote created by the wallet that the enote is also destined to.

#### Internal enotes

Enotes which are destined for the sending wallet and use a symmetric secret instead of a ECDH exchange are called "internal enotes". The most common type are `"change"` enotes, but internal `"payment"` enotes are also possible. For typical 2-output transactions, an internal enote reuses the same value of <code>D<sub>e</sub></code> as the other enote.

As specified above, these enotes use <code>s<sub>vb</sub></code> as the value for <code>s<sub>sr</sub></code>. The existence of internal enotes means that we have to effectively perform *two* types of balance recovery scan processes, external <code>s<sub>sr</sub></code> and internal <code>s<sub>sr</sub></code>. Note, however, that this does not necessarily make balance recovery twice as slow since one scalar-point multiplication and multiplication by eight in Ed25519 is significantly (~100x) slower than Blake2b hashing, and we get to skip those operations for internal scanning.

#### Special enotes

Special enotes are external self-send enotes in a 2-out transaction. The sender employs different shared secret derivations and Janus anchor derivations than a regular external enote.

#### Mandatory self-send enote rule

Every transaction that spends funds from the wallet must produce at least one self-send (not necessarily internal) enote, typically a change enote. If there is no change left, an enote is added with a zero amount. This ensures that all transactions relevant to the wallet have at least one output. This allows for remote-assist "light weight" wallet servers to serve *only* the transactions relevant to the wallet, including any transaction that has spent key images. This rule also helps to optimize full wallet multi-threaded scanning by reducing state reuse.

Even if a sender did not want to follow this rule, they would find that sending to two different, not-sender-owned addresses in a 2-out transaction is computationally intractable. During balance recovery, the recipient will attempt to recompute <code>D<sub>e</sub> ?= d<sub>e</sub> ConvertPubkeyE(K<sub>s</sub><sup>j</sup>)</code>. As such, sending to two external addresses would require finding `a, b` such that `a X = b Y` without knowing the discrete log between `X` and `Y`. This amounts to solving the discrete logarithm problem.

However, a sender may skirt this rule if the sender sends to the same to address twice in a 2-out transaction as long as they set <code>anchor<sub>norm</sub></code> equal to one another. This will result in the same ephemeral private key <code>d<sub>e</sub> = ScalarDerive("carrot_sending_key_normal" \|\| anchor<sub>norm</sub> \|\| input_context \|\| K<sub>s</sub><sup>j</sup> \|\| K<sub>v</sub><sup>j</sup> \|\| pid)</code>, and thus ephemeral pubkey, recomputed by the recipient each time on the two enotes.

#### One payment, one change rule

In a 2-out transaction, one enote's `enote_type` must be `"payment"`, and the other `"change"`.

In 2-out transactions, the ephemeral pubkey <code>D<sub>e</sub></code> is shared between enotes. `input_context` is also shared between the two enotes. Thus, if the two destination addresses share the same private view key <code>k<sub>v</sub></code> (which would happen if they both belonged to the sender) and the `enote_type` value is the same, then the amount blinding factors <code>k<sub>a</sub> = ScalarDerive("jamtis_commitment_mask" \|\| s<sub>sr</sub> \|\| input_context \|\| enote_type)</code> will be the same on both enotes, leading to trivially related amount commitments.

### Coinbase transactions

Coinbase transactions are not considered to be internal.

Miners should continue the practice of only allowing main addresses for the destinations of coinbase transactions in Carrot. This is because, unlike normal enotes, coinbase enotes do not contain an amount commitment, and thus scanning a coinbase enote commitment has no "hard target". If subaddresses can be the destinations of coinbase transactions, then the scanner *must* have their subaddress table loaded and populated to correctly scan coinbase enotes. If only main addresses are allowed, then the scanner does not need the table and can instead simply check whether <code>K<sub>s</sub><sup>0</sup> ?= K<sub>o</sub> - k<sub>g</sub><sup>o</sup> G + k<sub>t</sub><sup>o</sup> T</code>.

## Balance recovery

### Enote Scan

If this enote scan returns successfully, we will be able to recover the address spend pubkey, amount, and PID. Additionally, a successful return guarantees that A) the enote is uniquely addressed to our account, B) Janus attacks are mitigated, and C) burning bug attacks are mitigated. Note, however, that a successful return does *NOT* guarantee that the enote is spendable (i.e. that we will be able to recover `x, y` such that <code>K<sub>o</sub> = x G + y T</code>).

We perform the scan process once with <code>s<sub>sr</sub> = 8 k<sub>v</sub> D<sub>e</sub></code> (external), and once with <code>s<sub>sr</sub> = s<sub>vb</sub></code> (internal) if using the new key hierarchy.

1. Let <code>vt' = SecretDerive("jamtis_secondary_view_tag" \|\| s<sub>sr</sub> \|\| enote_nonce)</code>
1. If `vt' ≠ vt`, then <code><b>ABORT</b></code>
1. Let <code>s<sub>sr</sub><sup>ctx</sup> = SecretDerive("carrot_shared_secret_ctx" \|\| s<sub>sr</sub> \|\| enote_nonce)</code>
1. If a coinbase enote, then let `a' = a`, let <code>k<sub>a</sub>' = 1</code>, and skip to step 13
1. Let <code>m<sub>a</sub> = SecretDerive("jamtis_encryption_mask_a" \|\| s<sub>sr</sub><sup>ctx</sup>)</code>
1. Let <code>a' = a<sub>enc</sub> ⊕ m<sub>a</sub></code>
1. Let <code>k<sub>a</sub>' = ScalarDerive("jamtis_commitment_mask" \|\| s<sub>sr</sub> \|\| input_context \|\| "payment")</code>
1. Let <code>C<sub>a</sub>' = k<sub>a</sub>' G + a' H</code>
1. If <code>C<sub>a</sub>' == C<sub>a</sub></code>, then jump to step 13
1. Let <code>k<sub>a</sub>' = ScalarDerive("jamtis_commitment_mask" \|\| s<sub>sr</sub> \|\| input_context \|\| "change")</code>
1. Let <code>C<sub>a</sub>' = k<sub>a</sub>' G + a' H</code>
1. If <code>C<sub>a</sub>' ≠ C<sub>a</sub></code>, then <code><b>ABORT</b></code>
1. Let <code>k<sub>g</sub><sup>o</sup>' = ScalarDerive("jamtis_key_extension_g" \|\| s<sub>sr</sub><sup>ctx</sup>)</code>
1. Let <code>k<sub>t</sub><sup>o</sup>' = ScalarDerive("jamtis_key_extension_t" \|\| s<sub>sr</sub><sup>ctx</sup>)</code>
1. Let <code>K<sub>s</sub><sup>j</sup>' = K<sub>o</sub> - k<sub>g</sub><sup>o</sup>' G - k<sub>t</sub><sup>o</sup>' T</code>
1. If a coinbase enote and <code>K<sub>s</sub><sup>j</sup>' ≠ K<sub>s</sub></code>, then <code><b>ABORT</b></code>
1. If <code>s<sub>sr</sub> == s<sub>vb</sub></code> (i.e. performing an internal scan), then jump to step 33
1. Let <code>m<sub>pid</sub> = SecretDerive("jamtis_encryption_mask_pid" \|\| s<sub>sr</sub><sup>ctx</sup>)</code>
1. Set <code>pid' = pid<sub>enc</sub> ⊕ m<sub>pid</sub></code>
1. Let <code>m<sub>anchor</sub> = SecretDerive("jamtis_encryption_mask_j'" \|\| s<sub>sr</sub><sup>ctx</sup>)</code>
1. Let <code>anchor' = anchor<sub>enc</sub> ⊕ m<sub>anchor</sub></code>
1. If <code>K<sub>s</sub><sup>j</sup>' == K<sub>s</sub></code>, then let <code>K<sub>base</sub> = G</code>, else let <code>K<sub>base</sub> = K<sub>s</sub><sup>j</sup>'</code>
1. Let <code>K<sub>v</sub><sup>j</sup>' = k<sub>v</sub> K<sub>base</sub></code>
1. Let <code>d<sub>e</sub>' = ScalarDerive("carrot_sending_key_normal" \|\| anchor' \|\| input_context \|\| K<sub>s</sub><sup>j</sup>' \|\| K<sub>v</sub><sup>j</sup>' \|\| pid')</code>
1. Let <code>D<sub>e</sub>' = ConvertPubkeyE(d<sub>e</sub>' K<sub>base</sub>)</code>
1. If <code>D<sub>e</sub>' == D<sub>e</sub></code>, then jump to step 33
1. Set `pid' = nullpid`
1. Let <code>d<sub>e</sub>' = ScalarDerive("carrot_sending_key_normal" \|\| anchor' \|\| input_context \|\| K<sub>s</sub><sup>j</sup>' \|\| K<sub>v</sub><sup>j</sup>' \|\| pid')</code>
1. Let <code>D<sub>e</sub>' = ConvertPubkeyE(d<sub>e</sub>' K<sub>base</sub>)</code>
1. If <code>D<sub>e</sub>' == D<sub>e</sub></code>, then jump to step 33
1. Let <code>anchor<sub>sp</sub> = SecretDerive("carrot_janus_anchor_special" \|\| D<sub>e</sub> \|\| enote_nonce \|\| k<sub>v</sub> \|\| K<sub>s</sub>)</code>
1. If <code>anchor' ≠ anchor<sub>sp</sub></code>, then <code><b>ABORT</b></code> (this was an attempted Janus attack!)
1. Return successfully!

### Determining spendability and computing key images

An enote is spendable if the computed nominal address spend pubkey <code>K<sub>s</sub><sup>j</sup>'</code> is one that we can actually derive. However, the enote scan process does not inform the sender how to derive the subaddress. One method of quickly checking whether a nominal address spend pubkey is derivable, and thus spendable, is a *subaddress table*. A subaddress table maps precomputed address spend pubkeys to their index `j`. Once the subaddress index for an enote is determined, we can begin computing the key image.

#### Legacy key hierarchy key images

If `j ≠ 0`, then let <code>k<sub>sub_ext</sub><sup>j</sup> = ScalarDeriveLegacy(IntToBytes64(8) \|\| k<sub>v</sub> \|\| IntToBytes32(j<sub>major</sub>) \|\| IntToBytes32(j<sub>minor</sub>))</code>, otherwise let <code>k<sub>sub_ext</sub><sup>j</sup> = 0</code>.

The key image is computed as: <code>L = (k<sub>s</sub> + k<sub>sub_ext</sub><sup>j</sup> + k<sub>g</sub><sup>o</sup>) H<sub>p</sub><sup>2</sup>(K<sub>o</sub>)</code>.

#### New key hierarchy key images

If `j ≠ 0`, then let <code>k<sub>a</sub><sup>j</sup> = ScalarDerive("carrot_subaddress_scalar" \|\| s<sub>gen</sub><sup>j</sup> \|\| K<sub>s</sub> \|\| K<sub>v</sub> \|\| IntToBytes32(j<sub>major</sub>) \|\| IntToBytes32(j<sub>minor</sub>))</code>, otherwise let <code>k<sub>a</sub><sup>j</sup> = 1</code>.

The key image is computed as: <code>L = (k<sub>gi</sub> * k<sub>a</sub><sup>j</sup> + k<sub>g</sub><sup>o</sup>) H<sub>p</sub><sup>2</sup>(K<sub>o</sub>)</code>.

### Handling key images and calculating balance

If a scanner successfully scans any enote within a transaction, they should save all those key images indefinitely as "potentially spent". The rest of the ledger's key images can be discarded. Then, the key images for each enote should be calculated. The "unspent" enotes are determined as those whose key images is not within the set of potentially spent key images. The sum total of the amounts of these enotes is the current balance of the wallet, and the unspent enotes can be used in future input proofs.

## Security properties

Below are listed some security properties which are to hold for Carrot. Unless otherwise specified, it is assumed that no participant can efficiently solve the decisional Diffie-Hellman problem in Curve25519 and Ed25519 (i.e. the decisional Diffie-Hellman assumption [[citation](https://crypto.stanford.edu/~dabo/pubs/papers/DDH.pdf)] holds).

### Balance recovery security

The term "honest receiver" below means an entity with certain private key material correctly executing the balance recovery instructions of the addressing protocol as described above. A receiver who correctly follows balance recovery instructions but lies to the sender whether they received funds is still considered "honest". Likewise, an "honest sender" is an entity who follows the sending instructions of the addressing protocol as described above.

#### Completeness

An honest sender who sends amount `a` and payment ID `pid` to address <code>(is_main, K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>)</code>, internally or externally, can be guaranteed that the honest receiver who derived that address will:

1. Recover the same <code>a, pid, K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup></code>
2. Recover `x, y, z` such that <code>C<sub>a</sub> = z G + a H</code> and <code>K<sub>o</sub> = x G + y T</code>

This is to be achieved without any other interactivity.

#### Spend Binding

If an honest receiver recovers `x` and `y` for an enote such that <code>K<sub>o</sub> = x G + y T</code>, then it is guaranteed within a security factor that no other entity without knowledge of <code>k<sub>ps</sub></code> (or <code>k<sub>s</sub></code> for legacy key hierarchies) will also be able to find `x` and `y`.

#### Amount Commitment Binding

If an honest receiver recovers `z` and `a` for an non-coinbase enote such that <code>C<sub>a</sub> = z G + a H</code>, then it is guaranteed within a security factor that no other entity without knowledge of <code>k<sub>v</sub></code> or <code>d<sub>e</sub></code> will also be able to find `z`.

#### Burning Bug Resistance

For any <code>K<sub>o</sub></code>, it is computationally intractable to find two unique values of `input_context` such that an honest receiver will determine both enotes to be spendable. Recall that spendability is determined as whether <code>K<sub>s</sub><sup>j</sup>' = K<sub>o</sub> - k<sub>g</sub><sup>o</sup> G - k<sub>t</sub><sup>o</sup> T</code> is an address spend pubkey that we can normally derive from our account secrets.

#### Janus Attack Resistance

There is no algorithm that, without knowledge of the recipient's private view key <code>k<sub>v</sub></code>, allows a sender to construct an enote using two or more honestly-derived non-integrated addresses which successfully passes the enote scan process when the two addresses where derived from the same account, but fails when the addresses are unrelated.

More concretely, it is computationally intractable, without knowledge of the recipient's private view key <code>k<sub>v</sub></code>, to construct an external enote which successfully passes the enote scan process such that the recipient's computed nominal address spend pubkey <code>K<sub>s</sub><sup>j</sup>' = K<sub>o</sub> - k<sub>g</sub><sup>o</sup> G - k<sub>t</sub><sup>o</sup> T</code> does not match the shared secret <code>s<sub>sr</sub> = 8 r ConvertPubkeyE(K<sub>v</sub><sup>j</sup>')</code> for some sender-chosen `r`. This narrowed statement makes the informal assumption that using the address view spend pubkey for the Diffie-Hellman exchange and nominally recomputing its correct address spend pubkey leaves no room for a Janus attack.

### Unlinkability

#### Computational Address-Address Unlinkability

A third party cannot determine if two non-integrated addresses share the same <code>k<sub>v</sub></code> with any better probability than random guessing.

#### Computational Address-Enote Unlinkability

A third party cannot determine if an address is the destination of an enote with any better probability than random guessing, even if they know the destination address.

#### Computational Enote-Enote Unlinkability

A third party cannot determine if two enotes have the same destination address with any better probability than random guessing, even if they know the destination address.

#### Computational Enote-Key Image Unlinkability

A third party cannot determine if any key image is *the* key image for any enote with any better probability than random guessing, even if they know the destination address.

### Forward Secrecy

Forward secrecy refers to the preservation of privacy properties of past transactions against a future adversary capable of solving the elliptic curve discrete logarithm problem (ECDLP), for example a quantum computer. We refer to an entity with this capability as a *SDLP* (Solver of the Discrete Log Problem). We assume that the properties of secure hash functions still apply to SDLPs (i.e. collision-resistance, preimage-resistance, one-way).

#### Address-Conditional Forward Secrecy

A SDLP can learn no receiver or amount information about a transaction output, nor where it is spent, without knowing a receiver's public address.

#### Internal Forward Secrecy

Even with knowledge of <code>s<sub>ga</sub></code>, <code>k<sub>ps</sub></code>, <code>k<sub>gi</sub></code>, <code>k<sub>v</sub></code>, a SDLP without explicit knowledge of <code>s<sub>vb</sub></code> will not be able to discern where internal enotes are received, where/if they are spent, nor the amounts with any better probability than random guessing.

### Indistinguishability

We define multiple processes by which public value representations are created as "indistinguishable" if a SDLP, without knowledge of public addresses or private account keys, cannot determine by which process the public values were created with any better probability than random guessing. The processes in question are described below.

#### Transaction output random indistinguishability

Carrot transaction outputs are indistinguishable from random transaction outputs. The Carrot transaction output process is described earlier in this document. The random transaction output process is modeled as follows:

1. Sample <code>r<sub>1</sub></code> and <code>r<sub>2</sub></code> independently from uniform integer distribution `[0, ℓ)`.
2. Set <code>K<sub>o</sub> = r<sub>1</sub> G</code>
3. Set <code>C<sub>a</sub> = r<sub>2</sub> G</code>

#### Ephemeral pubkey random indistinguishability

Carrot ephemeral pubkeys are indistinguishable from random Curve25519 pubkeys. The Carrot ephemeral pubkey process is described earlier in this document. The random ephemeral pubkey process is modeled as follows:

1. Sample `r` from uniform integer distribution `[0, ℓ)`.
2. Set <code>D<sub>e</sub> = r B</code>

Note that in Carrot ephemeral pubkey construction, the ephemeral private key <code>d<sub>e</sub></code>, unlike most X25519 private keys, is derived without key clamping. Multiplying by this unclamped key makes it so the resultant pubkey is indistinguishable from a random pubkey (*needs better formalizing*).

#### Other enote component random indistinguishability

The remaining Carrot enote components are indistinguishable from random byte strings. The Carrot enote process is described earlier in this document. The random enote byte string process is modeled as follows:

1. Sample <code>a<sub>enc</sub> = RandBytes(8)</code>
2. Sample <code>anchor<sub>enc</sub> = RandBytes(16)</code>
3. Sample <code>vt = RandBytes(3)</code>
4. Sample <code>pid<sub>enc</sub> = RandBytes(8)</code>

## Credits

Special thanks to everyone who commented and provided feedback on the original [Jamtis gist](https://gist.github.com/tevador/50160d160d24cfc6c52ae02eb3d17024). Many of the ideas were incorporated in this document.

A *very* special thanks to @tevador, who wrote up the Jamtis and Jamtis-RCT specifications, which were the foundation of this document, containing most of the transaction protocol math.

## Glossary

- *Amount Commitment* - An elliptic curve point, in the form of a Pederson Commitment [[citation](https://www.getmonero.org/resources/moneropedia/pedersen-commitment.html)], which is used to represent hidden amounts in transaction outputs in RingCT and FCMP++
- *Burning Bug Attack* - An attack where an exploiter duplicates an output pubkey and tricks the recipient into accepting both, even though only one can be spent
- *Coinbase Transaction* - A transaction which has no key images, and plaintext integer amounts instead of amount commitments in its outputs
- *Cryptonote* - A cryptocurrency consensus protocol and addressing scheme which was the foundation for Monero's ledger interactions initially
- *Cryptonote Address* - An address in the form described in the Cryptonote v2 whitepaper
- *Enote* - A transaction output and its associated data unique to that transaction output
- *Ephemeral Public Key* - An elliptic curve point associated to transaction outputs in order to hide enote details through a Diffie-Hellman key exchange
- *External Enote* - An enote which was constructed by performing an asymmetric Elliptic Curve Diffie-Hellman key exchange against an address, main or subaddress
- *FCMP++* - A proposed cryptocurrency consensus protocol to upgrade Monero's RingCT consensus protocol
- *Forward Secrecy* - The property of a cryptographic construction that information is hidden from an observer that can efficiently solve the Discrete Logarithm Problem 
- *Indistinguishability* - The property of multiple cryptographic constructions that the public values posted cannot be determined to the result of any single construction
- *Input Content* - A unique value associated to each transaction used in the Carrot address protocol derivations to mitigate burning bug attacks
- *Integrated Address* - A main address which additionally contains a payment ID
- *Internal Enote* - An enote which was constructed using a symmetric shared secret, typically the view-balance secret
- *Janus Anchor* - An enote component whose purpose is two fold in mitigating Janus attacks: act as an entropy source for deriving the ephemeral private key or act as an HMAC validating the ephemeral pubkey
- *Janus Attack* - An attack where an exploiter constructs an enote partially using two different addresses they suspect to belong to the same user such that the confirmation of that payment confirms the addresses are actually related
- *Key Image* - An elliptic curve point emitted during a Rerandomizable RingCT spend proof, used during balance recovery to determine whether an enote has been spent yet
- *Ledger* - An immutable, append-only list of transactions which is the shared medium of data exchange for different participants of the network
- *Main Address* - same as *Cryptonote Address*
- *Monero* - A payment network, along with a cryptocurrency *XMR*, that historically utilizes a collection of consensus protocols on its ledger, namely: Cryptonote, RingCT, and FCMP++
- *Payment ID* - An 8 byte array included with transaction data used to differentiate senders
- *Rerandomizable RingCT* - An abstraction of FCMP++ defined in this document that allows the formalization of different security properties without knowledge of the underlying proving system
- *RingCT* - A cryptocurrency consensus protocol that iterated on Cryptonote by introducing hidden amounts by way of amount commitments
- *Self-send Enote* - An enote constructed by wallet intended to be received by the same wallet, either internal or external
- *Special Enote* - An external self-send enote within a 2-output transaction
- *Subaddress* - An address form introduced by Monero contributors which allows for a single wallet to generate an arbitrary number of unlinkable addresses without affecting scanning speed
- *Transaction* - An atomic modification to the ledger containing key images, transaction outputs, and other unstructured data
- *Transaction Output* - A distinct tuple of an elliptic curve point and amount commitment or plaintext amount which is contained in a list in a transaction
- *View Tag* - A small enote component, calculated as a partial hash of the sender-receiver shared key, which is checked early in the balance recovery process to optimize scanning performance
- *Wallet* - A collection of private key data, cached ledger state, and other information which is used to interact with the shared ledger

## References

*INSERT REFERENCES HERE*

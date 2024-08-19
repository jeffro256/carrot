# Carrot

Carrot (Cryptonote Address on Rerandomizable-RingCT-Output Transactions) is an addressing protocol for the upcoming FCMP++ upgrade to Monero which maintains backwards compatibility with existing addresses. It does this while bringing new privacy and usability features, such as outgoing view keys. Carrot is not the only upcoming addressing protocol for Monero's FCMP++ consensus protocol. The other big contender is Jamtis, for which Carrot is designed to be indistinguishable on-chain, which will justify some seemingly strange design choices later on in this document. 

## 1. Background

### 1.1 Cryptonote Addresses, Integrated Addresses, and Subaddresses

Cryptonote addresses are a crucial component of Monero's privacy model, providing recipient unlinkability across transactions. Unlike Bitcoin, which uses transparent addresses, Monero's use of Cryptonote addresses ensures that all transaction outputs have unlinkable public keys regardless of the number of times an address is reused, and without requiring interactivity. In the beginning, since there was only one address per wallet, a method was needed for receivers to differentiate their senders. *Payment IDs*, an arbitrary 8 byte string attached to transactions, was the initial solution to this problem. *Integrated addresses* improved the UX of these payment IDs by including them inside of addresses. Wallets then started encrypting the payment IDs on-chain, and adding dummies if no payment IDs were used, which greatly improved privacy. In 2016, Monero iterated even further by introducing *subaddresses* [[1](https://github.com/monero-project/research-lab/issues/7)], an addressing scheme that existing wallets could adopt, allowing them to generate an arbitrary number of unlinkable receiving addresses without affecting scan speed.

### 1.2 FCMP++

To tackle privacy shortcomings with ring signatures, there is a consensus protocol update planned for Monero called FCMP++, which allows for an "anonymity set" of the entire chain. This protocol leverages a primitive for set membership called *Curve Trees*. Curve Trees allows one to efficiently prove that a "rerandomized" curve point exists in some set without revealing the element. In Monero, this set is defined as all "spendable" (i.e. unlocked and valid) transaction outputs on-chain. This randomization transformation is similar to "blinding" coin amounts in Pederson Commitments, and as a side effect, transaction output public keys *themselves* can be rerandomized on-chain. This fact opens the door for addressing protocols to add long-desired features, namely forward secrecy and outgoing view keys.

## 2. New Features

### 2.1 Address generator

This tier is intended for merchant point-of-sale terminals. It can generate addresses on demand, but otherwise has no access to the wallet (i.e. it cannot recognize any payments in the blockchain).

### 2.2 Payment validator wallets

Carrot supports view-incoming-only wallets that can verify that an external payment was received into the wallet, without the ability to see where those payment enotes were spent, or spend it themselves. But unlike old Monero view-only wallets, a Carrot payment validator wallet cannot see *"internal"* change enotes.

### 2.3 Full view-only wallets

Carrot supports full view-only wallets that can identify spent outputs (unlike legacy view-only wallets), so they can display the correct wallet balance and list all incoming and outgoing transactions.

### 2.4 Janus attack mitigation

A Janus attack [[2](https://web.getmonero.org/2019/10/18/subaddress-janus.html)] is a targeted attack that aims to determine if two addresses A, B belong to the same wallet. Janus outputs are crafted in such a way that they appear to the recipient as being received to the wallet address B, while secretly using a key from address A. If the recipient confirms the receipt of the payment, the sender learns that they own both addresses A and B.

Carrot prevents this attack by allowing the recipient to recognize a Janus output.

### 2.5 Address-conditional forward secrecy

As a result of leveraging the FCMP++ consensus protocol, Carrot has the ability to hide all transaction details (sender, receiver, amount) from third-party observers with the ability to solve the discrete log problem (e.g. quantum computers), as long as the observer does not know receiver's addresses.

### 2.6 Internal forward secrecy

Enotes that are sent "internally" to one's own wallet will have all transactions details hidden (sender, receiver, amount) from third-party observers with the ability to solve the discrete log problem (e.g. quantum computers), even if the observer has knowledge of the receiver's address.

### 2.7 Payment ID confirmation

Payment IDs are confirmed by a cryptographic hash, which gives integrated address payment processors better guarantees, provides better UX, and allows many-output batched transactions to unambiguously include an integrated address destination.

## 3. Notation

### 3.1 Miscellaneous definitions

1. The function `BytesToInt256(x)` deserializes a 256-bit little-endian integer from a 32-byte input.
1. The function `BytesToInt512(x)` deserializes a 512-bit little-endian integer from a 64-byte input.
1. The function `IntToBytes8(x)` serializes an integer into a little-endian encoded 8-byte output.
1. The function `IntToBytes4(x)` serializes an integer into a little-endian encoded 4-byte output.
1. The function `RandBytes(x)` generates a random x-byte string.
1. Concatenation is denoted by `||`.
1. Bit-wise XOR (exclusive-or) is denoted by `⊕`.

### 3.2 Hash functions

The function <code>H<sub>b</sub>(x)</code> with parameters `b, x`, refers to the Blake2b hash function [[3](https://eprint.iacr.org/2013/322.pdf)] initialized as follows:

* The output length is set to `b` bytes.
* Hashing is done in sequential mode.
* The Personalization string is set to the ASCII value "Monero", padded with zero bytes.
* The input `x` is hashed.

The function `SecretDerive` is defined as:

<code>SecretDerive(x) = H<sub>32</sub>(x)</code>

The function `Keccak256(x)` refers to the SHA3-256 variant (AKA `r = 1088, c = 512, d = 256`) of the Keccak function [[4](https://keccak.team/keccak.html)].

### 3.3 Elliptic curves

Two elliptic curves are used in this specification:

1. **Curve25519** - a Montgomery curve. Points on this curve include a cyclic subgroup <code>𝔾<sub>1</sub></code>.
1. **Ed25519** - a twisted Edwards curve. Points on this curve include a cyclic subgroup <code>𝔾<sub>2</sub></code>.

Both curves are birationally equivalent, so the subgroups <code>𝔾<sub>1</sub></code> and <code>𝔾<sub>2</sub></code> have the same prime order <code>ℓ = 2<sup>252</sup> + 27742317777372353535851937790883648493</code>. The total number of points on each curve is `8ℓ`.

#### 3.3.1 Curve25519

Curve25519 is used exclusively to serialize the Diffie-Hellman ephemeral pubkey [[5](https://cr.yp.to/ecdh/curve25519-20060209.pdf)] in transactions to match Jamtis behavior.

Public keys (elements of <code>𝔾<sub>1</sub></code>) are denoted by the capital letter `D` and are serialized as the x-coordinate of the corresponding Curve25519 point. Scalar multiplication is denoted by a space, e.g. <code>D = d B</code>.

#### 3.3.2 Ed25519

The Edwards curve is used for signatures and more complex cryptographic protocols [[6](https://ed25519.cr.yp.to/ed25519-20110926.pdf)]. The following generators are used:

|Point|Derivation|Serialized (hex)|
|-----|----------|----------|
| `G` | generator of <code>𝔾<sub>2</sub></code> | `5866666666666666666666666666666666666666666666666666666666666666`
| `H` | <code>H<sub>p</sub><sup>1</sup>(G)</code> | `8b655970153799af2aeadc9ff1add0ea6c7251d54154cfa92c173a0dd39c1f94`
| `T` | <code>H<sub>p</sub><sup>2</sup>(Keccak256("Monero generator T"))</code> | `966fc66b82cd56cf85eaec801c42845f5f408878d1561e00d3d7ded2794d094f`

Here <code>H<sub>p</sub><sup>1</sup></code> and <code>H<sub>p</sub><sup>2</sup></code> refer to two hash-to-point functions on Ed25519.

Private keys for Ed25519 are 32-byte integers denoted by a lowercase letter `k`. They are generated using one of the two following functions:

1. <code>KeyDerive2(x) = BytesToInt512(H<sub>64</sub>(x)) mod ℓ</code>
1. <code>KeyDerive2Legacy(x) = BytesToInt256(Keccak256(x)) mod ℓ</code>

Public keys (elements of <code>𝔾<sub>2</sub></code>) are denoted by the capital letter `K` and are serialized as 256-bit integers, with the lower 255 bits being the y-coordinate of the corresponding Ed25519 point and the most significant bit being the parity of the x-coordinate. Scalar multiplication is denoted by a space, e.g. <code>K = k G</code>.

#### 3.3.3 Public key conversion

We define two functions that can transform public keys between the two curves:

1. `ConvertPubkey1(D)` takes a Curve25519 public key `D` and outputs the corresponding Ed25519 public key `K` with an even-valued `x` coordinate.
2. `ConvertPubkey2(K)` takes an Ed25519 public key `K` and outputs the corresponding Curve25519 public key `D`.

The conversions between points on the curves are done with the equivalence `y = (u - 1) / (u + 1)`, where `y` is the Ed25519 y-coordinate and `u` is the Curve25519 x-coordinate. Notice that the x-coordinates of Ed25519 points and the y-coordinates of Curve25519 points are not considered.

Additionally, we define the function `NormalizeX(K)` that takes an Ed25519 point `K` and returns `K` if its `x` coordinate is even or `-K` if its `x` coordinate is odd.

## 4. Rerandomizable RingCT abstraction

Here we formally define an abstraction of the FCMP++ consensus layer called *Rerandomizable RingCT* which lays out the requirements that Carrot needs. All elliptic curve arithmetic occurs on Ed25519.

### 4.1 Creating a transaction output

Transaction outputs are defined as the two points <code>(K<sub>o</sub>, C<sub>a</sub>)</code>. To create a valid transaction output, the sender must know `z, a` such that <code>C<sub>a</sub> = z G + a H</code> where <code>0 ≤ a < 2<sup>64</sup></code>. Coinbase transactions have a plaintext integer amount `a` instead of the amount commitment <code>C<sub>a</sub></code>, which is implied to be <code>C<sub>a</sub> = G + a H</code>.

### 4.2 Spending a transaction output

To spend this output, the recipient must know `x, y, z, a` such that <code>K<sub>o</sub> = x G + y T</code> and <code>C<sub>a</sub> = z G + a H</code> where <code>0 ≤ a < 2<sup>64</sup></code>. Spending an output necessarily emits a *key image* (AKA *"linking tag"* or *"nullifier"*) <code>L = x H<sub>p</sub><sup>2</sup>(K<sub>o</sub>)</code>. All key images must be in the prime order subgroup <code>𝔾<sub>2</sub></code>.

### 4.3 Transaction model

Transactions contain a list of outputs, a list of key images, and additional unstructured data. All output pubkeys <code>K<sub>o</sub></code> and key images `L` must be unique within a transaction. 

### 4.4 Ledger model

The ledger can be modeled as an append-only list of transactions. Transactions can only contain key images of transaction outputs of "lower" positions within the ledger list. No two key images in any transaction in the ledger are ever equal to each other. In practice, the ledger will contain additional cryptographic proofs that verify the integrity of the data within each transaction, but those can largely be ignored for this addressing protocol.

## 5. Wallets

### 5.1 Legacy key hierarchy

The following figure shows the overall hierarchy used for legacy wallet keys. Note that the master secret <code>s<sub>m</sub></code> doesn't exist for multi-signature wallets. <code>k<sub>v</sub></code> will also be derived separately from <code>k<sub>s</sub></code>.

```
s_m (master secret)
 |
 |
 |
 +- k_s (spend key)
     |
     |
     |
     +- k_v (view key)
```

| Key | Name | Derivation | Used to |
|-----|------|------------|---------|
|<code>k<sub>s</sub></code> | spend key | <code>k<sub>s</sub> = BytesToInt256(s<sub>m</sub>) mod ℓ</code> | generate key images and spend enotes                 |
|<code>k<sub>v</sub></code> | view key  | <code>k<sub>v</sub> = KeyDerive2Legacy(k<sub>s</sub>)</code>    | find and decode received enotes, generate addresses |

### 5.2 New key hierarchy

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
     +- k_v (view key)
     |
     |
     |
     +- s_ga (generate-address secret)
```

| Key | Name | Derivation | Used to |
|-----|------|------------|-------|
|<code>k<sub>ps</sub></code> | prove-spend key         | <code>k<sub>ps</sub> = KeyDerive2("jamtis_prove_spend_key" \|\| s<sub>m</sub>)</code>                  | spend enotes |
|<code>k<sub>gi</sub></code> | generate-image key      | <code>k<sub>gi</sub> = KeyDerive2("jamtis_generate_image_key" \|\| s<sub>vb</sub>)</code>              | generate key images |
|<code>k<sub>v</sub></code>  | view key                | <code>k<sub>v</sub> = KeyDerive2("carrot_view_key" \|\| s<sub>vb</sub>)</code>                         | find and decode received enotes |
|<code>s<sub>ga</sub></code> | generate-address secret | <code>s<sub>ga</sub> = SecretDerive</sub>("jamtis_generate_address_secret" \|\| s<sub>vb</sub>)</code> | generate addresses |

### 5.3 New wallet public keys

There are 2 global wallet public keys for the new private key hierarchy. These keys are not usually published, but are needed by lower wallet tiers.

| Key | Name | Value |
|-----|------|-------|
|<code>K<sub>s</sub></code> | spend key    | <code>K<sub>s</sub> = k<sub>gi</sub> G + k<sub>ps</sub> T</code></code> |
|<code>K<sub>v</sub></code> | view key     | <code>K<sub>v</sub> = k<sub>v</sub> K<sub>s</sub></code>                |

Note: for legacy key hierarchies, <code>K<sub>s</sub> = k<sub>s</sub> G</code>.

### 5.4 New wallet access tiers

The new private key hierarchy enables the following useful wallet tiers:

| Tier             | Secret                      | Off-chain capabilities    | On-chain capabilities |
|------------------|-----------------------------|---------------------------|-----------------------|
| Generate-Address | <code>s<sub>ga</sub></code> | generate public addresses | none                  |
| View-Received    | <code>k<sub>v</sub>         | all                       | view received         |
| View-All         | <code>s<sub>vb</sub></code> | all                       | view all              |
| Master           | <code>s<sub>m</sub></code>  | all                       | all                   |

#### 5.4.1 Generate-Address

This wallet tier can generate public addresses for the wallet. It doesn't provide any blockchain access.

#### 5.4.2 View-Received

This level provides the wallet with the ability to see all incoming payments, but cannot see any outgoing payments and change outputs. It can be used for payment processing or auditing purposes.

#### 5.4.3 View-All

This is a full view-only wallet than can see all incoming and outgoing payments (and thus can calculate the correct wallet balance).

#### 5.4.4 Master wallet (Master)

This tier has full control of the wallet.

## 6. Addresses

### 6.1 Address generation

There are two types of Cryptonote addresses: main addresses and subaddresses. There can only be a maximum of one main address per view key, but any number of subaddresses. However, by convention, subaddresses are generated from a "subaddress index", which is a tuple of two 32-bit unsigned integers <code>(j<sub>major</sub>, j<sub>minor</sub>)</code>, which allows for 2<sup>64</sup> addresses. The reason for the distinction between <code>j<sub>major</sub></code> and <code>j<sub>minor</sub></code> is simply for UX reasons. The "major" index is used to make separate "accounts" per wallet, which is used to compartmentalize input selection, change outputs, etc. The subaddress index `(0, 0)` is used to designate the main address, even though the key derivation is different. For brevity's sake, we use the label `j` as shorthand for <code>(j<sub>major</sub>, j<sub>minor</sub>)</code> and `0` as a shorthand for `(0, 0)`.

Each Cryptonote address derived from index `j` encodes the tuple <code>(K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>)</code>.

#### 6.1.1 Main address keys

The two public keys of the main address are constructed as:

* <code>K<sub>s</sub><sup>0</sup> = K<sub>s</sub></code>
* <code>K<sub>v</sub><sup>0</sup> = k<sub>v</sub> G</code>

#### 6.1.2 Subaddress keys (Legacy Hierarchy)

Under the legacy key hierarchy, the two public keys of a subaddress are constructed as:

* <code>K<sub>s</sub><sup>j</sup> = K<sub>s</sub> + k<sub>subext</sub><sup>j</sup> G</code>
* <code>K<sub>v</sub><sup>j</sup> = k<sub>v</sub> K<sub>s</sub><sup>j</sup></code>

Where subaddress extension key <code>k<sub>subext</sub><sup>j</sup> = KeyDerive2Legacy(IntToBytes8(8) \|\| k<sub>v</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code>. Notice that generating new subaddresses requires View-Received access to the wallet.

#### 6.1.3 Subaddress keys (New Hierarchy)

Under the new key hierarchy, the two public keys of a subaddress are constructed as:

* <code>K<sub>s</sub><sup>j</sup> = k<sub>a</sub><sup>j</sup> K<sub>s</sub></code>
* <code>K<sub>v</sub><sup>j</sup> = k<sub>a</sub><sup>j</sup> K<sub>v</sub></code>

Where address private key <code>k<sub>a</sub><sup>j</sup></code> are defined as follows:

| Symbol | Name | Definition |
|-------------------------- |-------------------------- |------------------------------|
|<code>k<sub>a</sub><sup>j</sup></code> | address private key  | <code>k<sub>a</sub><sup>j</sup> = KeyDerive2("jamtis_address_privkey" \|\| s<sub>gen</sub><sup>j</sup> \|\| K<sub>s</sub> \|\| K<sub>v</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code> |
| <code>s<sub>gen</sub><sup>j</sup></code> | address index generators | <code>s<sub>gen</sub><sup>j</sup> = SecretDerive("jamtis_address_index_generator" \|\| s<sub>ga</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code> |

The address index generator <code>s<sub>gen</sub><sup>j</sup></code> can be used to prove that the address was constructed from the index `j` and the public keys <code>K<sub>s</sub></code> and <code>K<sub>v</sub></code> without revealing <code>s<sub>ga</sub></code>.

#### 6.1.4 Integrated Addresses

Subaddresses are the recommended way to differentiate received enotes to your account for most users. However, there are some drawbacks to subaddresses. Most notably, in the past, generating subaddresses required View-Received access to the wallet (this is no longer the case with the new key hierarchy). This is not ideal for payment processors, so in practice a lot of processors turned to integrated addresses. Integrated addresses are simply main addresses with an 8-byte arbitrary string attached, called a *payment ID*. This payment ID is encrypted and then encoded into the transaction. In the reference wallet implementation, all transaction constructors who did not need to encode an encrypted payment ID into their transactions included a *dummy* payment ID by generating 8 random bytes. This makes the two types of sends indistinguishable on-chain from each other to external observers.

## 7. Transaction protocol

### 7.1 Transaction global fields

#### 7.1.1 Unlock time

The `unlock_time` field [[7](https://www.getmonero.org/resources/moneropedia/unlocktime.html)] should be disabled (i.e. set to 0), enforced by validator rule. This guarantees that enotes with valid <code>K<sub>o</sub></code> are always spendable after a sane period of time, an assumption which did not always hold true [[8](https://github.com/monero-project/research-lab/issues/78)].

#### 7.1.2 Payment ID

A single 8-byte encrypted payment ID field is retained for 2-output non-coinbase transactions for backwards compatibility with legacy integrated addresses. When not sending to a legacy integrated address, `pid` is set to zero.

The payment ID `pid` is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>pid</sub></code>. The encryption mask is derived from the shared secrets of the payment enote.

#### 7.1.3 View tag size specifier

A new 1-byte field `npbits` is added for future Jamtis transactions, but is unused in Carrot.

#### 7.1.4 Ephemeral public keys

Every 2-output transaction has one ephemeral public key <code>D<sub>e</sub></code>. Transactions with `N > 2` outputs have `N` ephemeral public keys (one for each output). Coinbase transactions always have one key per output.

### 7.2 Enote format

Each enote represents an amount `a` sent to a Cryptonote address <code>(K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>)</code>.

An enote contains the output public key <code>K<sub>o</sub></code>, the 3-byte view tag `vt`, the amount commitment <code>C<sub>a</sub></code>, encrypted *janus anchor* <code>anchor<sub>enc</sub></code>, and encrypted amount <code>a<sub>enc</sub></code>. For coinbase transactions, the amount commitment <code>C<sub>a</sub></code> is omitted and the amount is not encrypted.

#### 7.2.1 The output key

The output key is constructed as <code>K<sub>o</sub> = K<sub>s</sub><sup>j</sup> + k<sub>g</sub><sup>o</sup> G + k<sub>t</sub><sup>o</sup> T</code>, where <code>k<sub>g</sub><sup>o</sup></code> and <code>k<sub>t</sub><sup>o</sup></code> are output key extensions.

#### 7.2.2 View tags

The view tag `vt` is the first 3 bytes of a hash of the ECDH exchange with the view key. This view tag is used to fail quickly in the scan process for enotes not intended for the current wallet. The bit size of 24 was chosen as the fixed size because of Jamtis requirements.

#### 7.2.3 Amount commitment

The amount commitment is constructed as <code>C<sub>a</sub> = k<sub>a</sub> G + a H</code>, where <code>k<sub>a</sub></code> is the commitment mask and `a` is the amount. Coinbase transactions have implicitly <code>C<sub>a</sub> = a H + G</code>.

#### 7.2.4 Janus anchor

The Janus anchor `anchor` is a 16-byte encrypted string that provides protection against Janus attacks in Carrot. This space is to be used later for "address tags" in Jamtis. The anchor is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>anchor</sub></code>. In the case of normal transfers, <code>anchor=anchor<sup>nm</sup></code> is uniformly random, and used to re-derive the enote ephemeral private key <code>k<sub>e</sub></code> and check the enote ephemeral pubkey <code>D<sub>e</sub></code>. In *special* enotes, <code>anchor=anchor<sup>sp</sup></code> is set to the first 16 bytes of a hash of the tx components as well as the private view key <code>k<sub>v</sub></code>. Both of these derivation-and-check paths should only pass if either A) the sender constructed the enotes in a way which does not allow for a Janus attack or B) the sender knows the private view key, which would make a Janus attack pointless.

#### 7.2.5 Amount

The amount `a` is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>a</sub></code>.

### 7.3 Enote derivations

The enote components are derived from the shared secret keys <code>K<sub>d</sub></code> and <code>K<sub>d</sub><sup>ctx</code>. The definitions of these keys are described below.

| Component | Name   | Derivation |
|-----------|--------|-----------|
|<code>vt</code>|view tag| <code>vt = SecretDerive("jamtis_secondary_view_tag" \|\| K<sub>d</sub> \|\| K<sub>o</sub>)</code> |
|<code>m<sub>anchor</sub></code>|encryption mask for `anchor`| <code>m<sub>anchor</sub> = SecretDerive("jamtis_encryption_mask_j'" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub>)</code> |
|<code>m<sub>a</sub></code>|encryption mask for `a`| <code>m<sub>a</sub> = SecretDerive("jamtis_encryption_mask_a" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub>)</code> |
|<code>m<sub>pid</sub></code>|encryption mask for `pid`| <code>m<sub>pid</sub> = SecretDerive("jamtis_encryption_mask_pid" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub>)</code> |
|<code>k<sub>a</sub></code>|amount commitment blinding factor| <code>k<sub>a</sub> = KeyDerive2("jamtis_commitment_mask" \|\| K<sub>d</sub><sup>ctx</sup> \|\| enote_type)</code> |
|<code>k<sub>g</sub><sup>o</sup></code>|output key extension G| <code>k<sub>g</sub><sup>o</sup> = KeyDerive2("jamtis_key_extension_g" \|\| K<sub>d</sub><sup>ctx</sup> \|\| C<sub>a</sub>)</code> |
|<code>k<sub>t</sub><sup>o</sup></code>|output key extension T| <code>k<sub>t</sub><sup>o</sup> = KeyDerive2("jamtis_key_extension_t" \|\| K<sub>d</sub><sup>ctx</sup> \|\| C<sub>a</sub>)</code> |
|<code>anchor<sup>nm</sup></code>|janus anchor, normal| <code>anchor<sup>nm</sup> = RandBytes(16)</code> |
|<code>anchor<sup>sp</sup></code>|janus anchor, special| <code>anchor<sup>sp</sup> = SecretDerive("carrot_janus_anchor_special" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub> \|\| k<sub>v</sub> \|\| K<sub>s</sub>)</code> |
|<code>k<sub>e</sub></code>|ephemeral privkey| <code>k<sub>e</sub> = KeyDerive2("carrot_sending_key_normal" \|\| anchor<sup>nm</sup> \|\| a \|\| K<sub>s</sub><sup>j</sup> \|\| K<sub>v</sub><sup>j</sup> \|\| pid)</code> |

The variable `enote_type` is `"payment"` or `"change"` depending on the enote type. `pid` is set to `nullpid` (8 bytes of zeros) when not sending to an integrated address.

### 7.4 Ephemeral pubkey construction

The ephemeral pubkey <code>D<sub>e</sub></code>, a Curve25519 point, for a given enote is constructed differently based on what type of address one is sending to, how many outputs are in the transaction, and whether we are deriving on the internal or external path. Here "special" means an *external self-send* enote in
a 2-out transaction. "Normal" refers to non-special, non-internal enotes.

| Transfer Type            | <code>D<sub>e</sub></code> Derivation                                |
|--------------------------|----------------------------------------------------------------------|   
| Normal, to main address  | <code>ConvertPubkey2(k<sub>e</sub> G)</code>                         |
| Normal, to subaddress    | <code>ConvertPubkey2(k<sub>e</sub> K<sub>s</sub><sup>j</sup>)</code> |
| Internal                 | *any*                                                                |
| Special                  | <code>D<sub>e</sub><sup>other</sup></code>                           |

<code>D<sub>e</sub><sup>other</sup></code> refers to the ephemeral pubkey that would be derived on the *other* enote in a 2-out transaction. If both enotes in a 2-out transaction are "special", then no specific derivation of <code>D<sub>e</sub></code> is required. Internal enotes do not require any specific derivation for <code>D<sub>e</sub></code> either.

### 7.5 Sender-receiver shared secrets

The shared secret keys <code>K<sub>d</sub></code> and <code>K<sub>d</sub><sup>ctx</sup></code> are used to encrypt/extend all components of Carrot transactions. Most components (except for the view tag for performance reasons) use <code>K<sub>d</sub><sup>ctx</sup></code> to encrypt components.

<code>K<sub>d</sub></code> can be derived the following ways:

|                       | Derivation                                                           |
|---------------------- | ---------------------------------------------------------------------|
|Sender, external       |    <code>NormalizeX(8 k<sub>e</sub> K<sub>v</sub><sup>j</sup>)</code>|
|Recipient, external    |<code>NormalizeX(8 k<sub>v</sub> ConvertPubkey1(D<sub>e</sub>))</code>|
|Internal               |                                           <code>s<sub>vb</sub></code>|

Then, <code>K<sub>d</sub><sup>ctx</sup></code> is derived as <code>K<sub>d</sub><sup>ctx</sup> = SecretDerive("jamtis_sender_receiver_secret" \|\| K<sub>d</sub> \|\| D<sub>e</sub> \|\| input_context)</code>.

Here `input_context` is defined as:

| transaction type | `input_context` |
|------------------|---------------------------------|
| coinbase         | block height                    |
| non-coinbase     | sorted list of spent key images |

The purpose of `input_context` is to make <code>K<sub>d</sub><sup>ctx</sup></code> unique for every transaction. This helps protect against the burning bug.

### 7.6 Janus outputs

In case of a Janus attack, the recipient will derive different values of the enote ephemeral pubkey <code>D<sub>e</sub></code> and Janus `anchor`, and thus will not recognize the output.

### 7.7 Self-send enotes

Self-send enotes are any enote created by the wallet that the enote is also destined to.

#### 7.7.1 Internal enotes

Enotes which are destined for the sending wallet and use a symmetric secret instead of a ECDH exchange are called "internal enotes". The most common type are `"change"` enotes, but internal `"payment"` enotes are also possible. For typical 2-output transactions, an internal enote reuses the same value of <code>D<sub>e</sub></code> as the other enote.

As specified above, these enotes use <code>s<sub>vb</sub></code> as the value for <code>K<sub>d</sub></code>. The existence of internal enotes means that we have to effectively perform *two* types of balance recovery scan processes, external <code>K<sub>d</sub></code> and internal <code>K<sub>d</sub></code>. Note, however, that this does not necessarily make balance recovery twice as slow since one scalar-point multiplication and multiplication by eight in Ed25519 is significantly (~100x) slower than Blake2b hashing, and we get to skip those operations for internal scanning.

#### 7.7.2 Special enotes

Special enotes are external self-send enotes in a 2-out transaction. The sender employs different shared secret derivations and Janus anchor derivations than a regular external enote.

#### 7.7.3 Mandatory self-send enote rule

Every transaction that spends funds from the wallet must produce at least one self-send (not necessarily internal) enote, typically a change enote. If there is no change left, an enote is added with a zero amount. This ensures that all transactions relevant to the wallet have at least one output. This allows for remote-assist "light weight" wallet servers to serve *only* the transactions relevant to the wallet, including any transaction that has spent key images. This rule also helps to optimize full wallet multi-threaded scanning by reducing state reuse.

#### 7.7.4 One payment, one change rule

In a 2-out transaction with two internal or two special enotes, one enote's `enote_type` must be `"payment"`, and the other `"change"`.

In 2-out transactions, the ephemeral pubkey <code>D<sub>e</sub></code> is shared between enotes. `input_context` is also shared between the two enotes. Thus, if the two destination addresses share the same private view key <code>k<sub>v</sub></code> in a 2-out transaction, then <code>K<sub>d</sub><sup>ctx</sup></code> will be the same and the derivation paths will lead both enotes to have the same output pubkey, which is A) not allowed, B) bad for privacy, and C) would burn funds if allowed. However, note that the output pubkey extensions <code>k<sub>g</sub><sup>o</sup></code> and <code>k<sub>t</sub><sup>o</sup></code> bind to the amount commitment <code>C<sub>a</sub></code> which in turn binds to `enote_type`. Thus, if we want our two enotes to have unique derivations, then the `enote_type` needs to be unique.

### 7.8 Coinbase transactions

Coinbase transactions are not considered to be internal.

Miners should continue the practice of only allowing main addresses for the destinations of coinbase transactions in Carrot. This is because, unlike normal enotes, coinbase enotes do not contain an amount commitment, and thus scanning a coinbase enote commitment has no "hard target". If subaddresses can be the destinations of coinbase transactions, then the scanner *must* have their subaddress table loaded and populated to correctly scan coinbase enotes. If only main addresses are allowed, then the scanner does not need the table and can instead simply check whether <code>K<sub>s</sub><sup>0</sup> ?= K<sub>o</sub> - k<sub>g</sub><sup>o</sup> G + k<sub>t</sub><sup>o</sup></code>.

### 7.9 Scanning performance

When scanning for received enotes, legacy wallets need to calculate <code>NormalizeX(8 k<sub>v</sub> ConvertPubKey1(D<sub>e</sub>))</code>. The operation <code>ConvertPubKey1(D<sub>e</sub>)</code> can be done during point decompression for free. The `NormalizeX()` function simply drops the x coordinate. The scanning performance for legacy wallets is therefore the same as in the old protocol.

Note: Legacy wallets use scalar multiplication in <code>𝔾<sub>2</sub></code> because the legacy view key <code>k<sub>v</sub></code> might be larger than 2<sup>252</sup>, which is not supported in the Montgomery ladder.

## 8. Balance recovery

### 8.1 Enote Scan

If this enote scan returns successfully, we will be able to recover the address spend pubkey, amount, and PID. Additionally, a successful return guarantees that A) the enote is uniquely addressed to our account, B) Janus attacks are mitigated, and C) burning bug attacks are mitigated. Note, however, that a successful return does *NOT* guarantee that the enote is spendable (i.e. that we will be able to recover `x, y` such that <code>K<sub>o</sub> = x G + y T</code>).

We perform the scan process twice per enote, once with <code>K<sub>d</sub> = NormalizeX(8 k<sub>v</sub> ConvertPubkey1(D<sub>e</sub>))</code>, and once with <code>K<sub>d</sub> = s<sub>vb</sub></code>.

1. Let <code>vt' = SecretDerive("jamtis_secondary_view_tag" \|\| K<sub>d</sub> \|\| K<sub>o</sub>)</code>
1. If `vt' ≠ vt`, then <code><b>ABORT</b></code>
1. Let <code>K<sub>d</sub><sup>ctx</sup> = SecretDerive("jamtis_sender_receiver_secret" \|\| K<sub>d</sub> \|\| D<sub>e</sub> \|\| input_context)</code>
1. If a coinbase enote, then let `a' = a`, let <code>k<sub>a</sub>' = 1</code>, and skip to step 13
1. Let <code>m<sub>a</sub> = SecretDerive("jamtis_encryption_mask_a" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub>)</code>
1. Let <code>a' = a<sub>enc</sub> ⊕ m<sub>a</sub></code>
1. Let <code>k<sub>a</sub>' = KeyDerive2("jamtis_commitment_mask" \|\| K<sub>d</sub><sup>ctx</sup> \|\| "payment")</code>
1. Let <code>C<sub>a</sub>' = k<sub>a</sub>' G + a' H</code>
1. If <code>C<sub>a</sub>' == C<sub>a</sub></code>, then jump to step 13
1. Let <code>k<sub>a</sub>' = KeyDerive2("jamtis_commitment_mask" \|\| K<sub>d</sub><sup>ctx</sup> \|\| "change")</code>
1. Let <code>C<sub>a</sub>' = k<sub>a</sub>' G + a' H</code>
1. If <code>C<sub>a</sub>' ≠ C<sub>a</sub></code>, then <code><b>ABORT</b></code>
1. Let <code>k<sub>g</sub><sup>o</sup>' = KeyDerive2("jamtis_key_extension_g" \|\| K<sub>d</sub><sup>ctx</sup> \|\| C<sub>a</sub>)</code>
1. Let <code>k<sub>t</sub><sup>o</sup>' = KeyDerive2("jamtis_key_extension_t" \|\| K<sub>d</sub><sup>ctx</sup> \|\| C<sub>a</sub>)</code>
1. Let <code>K<sub>s</sub><sup>j</sup>' = K<sub>o</sub> - k<sub>g</sub><sup>o</sup>' G - k<sub>t</sub><sup>o</sup>' T</code>
1. If a coinbase enote and <code>K<sub>s</sub><sup>j</sup>' ≠ K<sub>s</sub></code>, then <code><b>ABORT</b></code>
1. Let <code>m<sub>pid</sub> = SecretDerive("jamtis_encryption_mask_pid" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub>)</code>
1. Set <code>pid' = pid<sub>enc</sub> ⊕ m<sub>pid</sub></code>
1. Let <code>m<sub>anchor</sub> = SecretDerive("jamtis_encryption_mask_j'" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub>)</code>
1. Let <code>anchor' = anchor<sub>enc</sub> ⊕ m<sub>anchor</sub></code>
1. If <code>K<sub>s</sub><sup>j</sup>' == K<sub>s</sub></code>, then let <code>K<sub>base</sub> = G</code>, else let <code>K<sub>base</sub> = K<sub>s</sub><sup>j</sup>'</code>
1. Let <code>K<sub>v</sub><sup>j</sup>' = k<sub>v</sub> K<sub>base</sub></code>
1. Let <code>k<sub>e</sub>' = KeyDerive2("carrot_sending_key_normal" \|\| anchor' \|\| a' \|\| K<sub>s</sub><sup>j</sup>' \|\| K<sub>v</sub><sup>j</sup>' \|\| pid')</code>
1. Let <code>D<sub>e</sub>' = ConvertPubkey2(k<sub>e</sub>' K<sub>base</sub>)</code>
1. If <code>D<sub>e</sub>' == D<sub>e</sub></code>, then jump to step 32
1. Set `pid' = nullpid`
1. Let <code>k<sub>e</sub>' = KeyDerive2("carrot_sending_key_normal" \|\| anchor' \|\| a' \|\| K<sub>s</sub><sup>j</sup>' \|\| K<sub>v</sub><sup>j</sup>' \|\| pid')</code>
1. Let <code>D<sub>e</sub>' = ConvertPubkey2(k<sub>e</sub>' K<sub>base</sub>)</code>
1. If <code>D<sub>e</sub>' == D<sub>e</sub></code>, then jump to step 32
1. Let <code>anchor<sup>sp</sup> = SecretDerive("carrot_janus_anchor_special" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub> \|\| k<sub>v</sub> \|\| K<sub>s</sub>)</code>
1. If <code>anchor' ≠ anchor<sup>sp</sup></code>, then <code><b>ABORT</b></code> (this was an attempted Janus attack!)
1. Return successfully!

### 8.2 Determining spendability and computing key images

An enote is spendable if the computed nominal address spend pubkey <code>K<sub>s</sub><sup>j</sup>'</code> is one that we can actually derive. However, the enote scan process does not inform the sender how to derive the subaddress. One method of quickly checking whether a nominal address spend pubkey is derivable, and thus spendable, is a *subaddress table*. A subaddress table maps precomputed address spend pubkeys to their index `j`. Once the subaddress index for an enote is determined, we can begin computing the key image.

#### 8.2.1 Legacy key hierarchy key images

If `j≠0`, then let <code>k<sub>subext</sub><sup>j</sup> = KeyDerive2Legacy(IntToBytes8(8) \|\| k<sub>v</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code>, otherwise let <code>k<sub>subext</sub><sup>j</sup> = 0</code>.

The key image is computed as: <code>L = (k<sub>s</sub> + k<sub>subext</sub><sup>j</sup> + k<sub>g</sub><sup>o</sup>) H<sub>p</sub><sup>2</sup>(K<sub>o</sub>)</code>.

#### 8.2.2 New key hierarchy key images

If `j≠0`, then let <code>k<sub>a</sub><sup>j</sup> = KeyDerive2("jamtis_address_privkey" \|\| s<sub>gen</sub><sup>j</sup> \|\| K<sub>s</sub> \|\| K<sub>v</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code>, otherwise let <code>k<sub>a</sub><sup>j</sup> = 1</code>.

The key image is computed as: <code>L = (k<sub>gi</sub> * k<sub>a</sub><sup>j</sup> + k<sub>g</sub><sup>o</sup>) H<sub>p</sub><sup>2</sup>(K<sub>o</sub>)</code>.

### 8.3 Handling key images and calculating balance

If a scanner successfully scans any enote within a transaction, they should save all those key images indefinitely as "potentially spent". The rest of the ledger's key images can be discarded. Then, the key images for each enote should be calculated. The "unspent" enotes are determined as those whose key images is not within the set of potentially spent key images. The sum total of the amounts of these enotes is the current balance of the wallet, and the unspent enotes can be used in future input proofs.

## 9. Security properties

### 9.1 Balance recovery security

The term "honest receiver" below means an entity with certain private key material correctly executing the balance recovery instructions of the addressing protocol as described above. A receiver who correctly follows balance recovery instructions but lies to the sender whether they received funds is still considered "honest". Likewise, an "honest sender" is an entity who follows the sending instructions of the addressing protocol as described above. In this subsection, all participants are assumed to adhere to the discrete log assumption.

#### 9.1.1 Completeness

An honest sender who sends amount `a` and payment ID `pid` to address <code>(K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>)</code>, internally or externally, can be guaranteed that the honest receiver who derived that address will:

1. Recover the same <code>a, pid, K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup></code>
2. Recover `x, y, z` such that <code>C<sub>a</sub> = z G + a H</code> and <code>K<sub>o</sub> = x G + y T</code>

This is to be achieved without any other interactivity.

#### 9.1.2 Spend Binding

If an honest receiver recovers `x` and `y` for an enote such that <code>K<sub>o</sub> = x G + y T</code>, then it is guaranteed within a security factor that no other entity without knowledge of <code>k<sub>ps</sub></code> (or <code>k<sub>s</sub></code> for legacy key hierarchies) will also be able to find `x` and `y`.

#### 9.1.3 Amount Commitment Binding

If an honest receiver recovers `z` and `a` for an non-coinbase enote such that <code>C<sub>a</sub> = z G + a H</code>, then it is guaranteed within a security factor that no other entity without knowledge of <code>k<sub>v</sub></code> or <code>k<sub>e</sub></code> will also be able to find `z`.

#### 9.1.4 Burning Bug Resistance

**Background**

The burning bug [[9](https://www.getmonero.org/2018/09/25/a-post-mortum-of-the-burning-bug.html)] is a undesirable result of Monero's old scan process wherein if an exploiter creates a transaction with the same ephemeral pubkey, output pubkey, and transaction output index as an existing transaction, a recipient will scan both instances of these enotes as "owned" and interpret their balance as increasing. However, since key images are linked to output pubkeys, the receiver can only spend one of these enotes, "burning" the other. If the exploiter creates an enote with amount `a = 0`, and the receiver happens to spend that enote first, then the receiver burns all of the funds in their original enote with only a tiny fee cost to the exploiter!

An initial patch [[10](https://github.com/monero-project/monero/pull/4438/files#diff-04cf14f64d2023c7f9cd7bd8e51dcb32ed400443c6a67535cb0105cfa2b62c3c)] was introduced secretly to catch when such an attempted attack occurred. However, this patch did not attempt to recover gracefully and instead simply stopped the wallet process with an error message. Further iterations of handling this bug automatically discarded all instances of duplicate output pubkeys which didn't have the greatest amount. However, all instances of burning bug handling in Monero Core require a complete view of all scanning history up to the current chain tip, which makes the workarounds somewhat fragile.

The original Jamtis addressing proposal [[11](https://gist.github.com/tevador/50160d160d24cfc6c52ae02eb3d17024)] by @tevador and the *Guaranteed Address* [[12](https://gist.github.com/kayabaNerve/8066c13f1fe1573286ba7a2fd79f6100)] proposal by @kayabaNerve were some of the first examples of addressing schemes where attempting a burn in this manner is inherently computationally intractable. Much like Carrot, these schemes somehow bind the output pubkey <code>K<sub>o</sub></code> to an `input_context` value, which is unique for every transaction. Thus, the receiver will only ever correctly determine an enote with output pubkey <code>K<sub>o</sub></code> to be spendable for a single value of `input_context`, avoiding the burning bug without ever having to maintain a complete scan state.

**Statement**

For any <code>K<sub>o</sub></code>, it is computationally intractable to find two unique values of `input_context` such that an honest receiver will determine both enotes to be spendable. Recall that spendability is determined as whether <code>K<sub>s</sub><sup>j</sup>' = K<sub>o</sub> - k<sub>g</sub><sup>o</sup> G - k<sub>t</sub><sup>o</sup> T</code> is an address spend pubkey that we can normally derive from our account secrets.

#### 9.1.5 Janus Attack Resistance

There is no algorithm that, without knowledge of the recipient's private view key <code>k<sub>v</sub></code>, allows a sender to construct an enote using two or more non-integrated addresses which successfully passes the enote scan process when the two addresses where derived from the same account, but fails when the addresses are unrelated.

More concretely, it is computationally intractable, without knowledge of the recipient's private view key <code>k<sub>v</sub></code>, to construct an external enote which successfully passes the enote scan process such that the recipient's computed nominal address spend pubkey <code>K<sub>s</sub><sup>j</sup>' = K<sub>o</sub> - k<sub>g</sub><sup>o</sup> G - k<sub>t</sub><sup>o</sup> T</code> does not match the shared secret <code>K<sub>d</sub> = NormalizeX(8 r K<sub>v</sub><sup>j</sup>')</code> for some sender-chosen `r`. This narrowed statement makes the informal assumption that using the address view spend pubkey for the Diffie-Hellman exchange and nominally recomputing its correct address spend pubkey leaves no room for a Janus attack.

### 9.2 Unlinkability

#### 9.2.1 Computational Address-Address Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if two non-integrated Cryptonote addresses share the same <code>k<sub>v</sub></code> with any better probability than random guessing.

#### 9.2.2 Computational Address-Enote Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if a Cryptonote addresses is the destination of an enote with any better probability than random guessing, even if they know the destination address.

#### 9.2.3 Computational Enote-Enote Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if two enotes have the same destination address with any better probability than random guessing, even if they know the destination address.

#### 9.2.4 Computational Enote-Key Image Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if any key image is *the* key image for any enote with any better probability than random guessing, even if they know the destination address.

### 9.3 Forward Secrecy

Forward secrecy refers to the preservation of privacy properties of past transactions against a future adversary capable of solving the elliptic curve discrete logarithm problem (ECDLP), for example a quantum computer. We refer to an entity with this capability as a *SDLP* (Solver of the Discrete Log Problem). We assume that the properties of secure hash functions still apply to SDLPs (i.e. collision-resistance, preimage-resistance, one-way).

#### 9.3.1 Address-Conditional Forward Secrecy

A SDLP can learn no receiver or amount information about a transaction output, nor where it is spent, without knowing a receiver's public address.

#### 9.3.2 Internal Forward Secrecy

Even with knowledge of <code>s<sub>ga</sub></code>, <code>k<sub>ps</sub></code>, <code>k<sub>gi</sub></code>, <code>k<sub>v</sub></code>, a SDLP without explicit knowledge of <code>s<sub>vb</sub></code> will not be able to discern where internal enotes are received, where/if they are spent, nor the amounts with any better probability than random guessing.

### 9.4 Indistinguishability

We define multiple processes by which public value representations are created as "indistinguishable" if a SDLP, without knowledge of public addresses or private account keys, cannot determine by which process the public values were created with any better probability than random guessing. The processes in question are described below.

#### 9.4.1 Transaction output random indistinguishability

Carrot transaction outputs are indistinguishable from random transaction outputs. The Carrot transaction output process is described earlier in this document. The random transaction output process is modeled as follows:

1. Sample <code>r<sub>1</sub></code> and <code>r<sub>2</sub></code> independently from uniform integer distribution `[0, ℓ)`.
2. Set <code>K<sub>o</sub> = r<sub>1</sub> G</code>
3. Set <code>C<sub>a</sub> = r<sub>2</sub> G</code>

#### 9.4.2 Ephemeral pubkey random indistinguishability

Carrot ephemeral pubkeys are indistinguishable from random Curve25519 pubkeys. The Carrot ephemeral pubkey process is described earlier in this document. The random ephemeral pubkey process is modeled as follows:

1. Sample `r` from uniform integer distribution `[0, ℓ)`.
2. Set <code>D<sub>e</sub> = r B</code>

Note that in Carrot ephemeral pubkey construction, the ephemeral privkey <code>k<sub>e</sub></code>, unlike most X25519 private keys, is derived without key clamping. Multiplying by this unclamped key makes it so the resultant pubkey is indistinguishable from a random pubkey (*needs better formalizing*).

#### 9.4.3 Other enote component random indistinguishability

The remaining Carrot enote components are indistinguishable from random byte strings. The Carrot enote process is described earlier in this document. The random enote byte string process is modeled as follows:

1. Sample <code>a<sub>enc</sub> = RandBytes(8)</code>
2. Sample <code>anchor<sub>enc</sub> = RandBytes(16)</code>
3. Sample <code>vt = RandBytes(3)</code>
4. Sample <code>pid<sub>enc</sub> = RandBytes(8)</code>

## 10. Credits

Special thanks to everyone who commented and provided feedback on the original [Jamtis gist](https://gist.github.com/tevador/50160d160d24cfc6c52ae02eb3d17024). Many of the ideas were incorporated in this document.

A *very* special thanks to @tevador, who wrote up the Jamtis and Jamtis-RCT specifications, which were the foundation of this document, containing most of the transaction protocol math.

## 11. References

1. https://github.com/monero-project/research-lab/issues/7
1. https://web.getmonero.org/2019/10/18/subaddress-janus.html
1. https://eprint.iacr.org/2013/322.pdf
1. https://keccak.team/keccak.html
1. https://cr.yp.to/ecdh/curve25519-20060209.pdf
1. https://ed25519.cr.yp.to/ed25519-20110926.pdf
1. https://www.getmonero.org/resources/moneropedia/unlocktime.html
1. https://github.com/monero-project/research-lab/issues/78
1. https://www.getmonero.org/2018/09/25/a-post-mortum-of-the-burning-bug.html
1. https://github.com/monero-project/monero/pull/4438/files#diff-04cf14f64d2023c7f9cd7bd8e51dcb32ed400443c6a67535cb0105cfa2b62c3c
1. https://gist.github.com/tevador/50160d160d24cfc6c52ae02eb3d17024
1. https://gist.github.com/kayabaNerve/8066c13f1fe1573286ba7a2fd79f6100

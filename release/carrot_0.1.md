# Carrot

Carrot (Cryptonote Address on Rerandomizable-RingCT-Output Transactions) is an addressing protocol for the upcoming FCMP++ upgrade to Monero which maintains backwards compatibility with existing addresses. It does this while bringing new privacy and usability features, such as outgoing view keys. Carrot is not the only upcoming addressing protocol for Monero's FCMP++ consensus protocol. The other big contender is Jamtis, for which Carrot is designed to be indistinguishable on-chain, which will justify some seemingly strange design choices later on in this document. 

## 1. Background

### 1.1 Cryptonote Addresses, Integrated Addresses, and Subaddresses

Cryptonote addresses are a crucial component of Monero's privacy model, providing recipient unlinkability across transactions. Unlike Bitcoin, which uses transparent addresses, Monero's use of Cryptonote addresses ensures that all transaction outputs have unlinkable public keys regardless of the number of times an address is reused, and without requiring interactivity. In the beginning, since there was only one address per wallet, a method was needed for receivers to differentiate their senders. *Payment IDs*, an arbitary 8 byte string attached to transactions, was the inital solution to this problem. *Integrated addresses* improved the UX of these payment IDs by including them inside of addresses. Wallets then started encrypting the payment IDs on-chain, and adding dummys if no payment IDs were used, which greatly improved privacy. In 2016, Monero [iterated](https://github.com/monero-project/research-lab/issues/7) even further by introducing *subaddresses*, an addressing scheme that existing wallets could adopt, allowing them to generate an arbitrary number of unlinkable receiving addresses without affecting scan speed.

### 1.2 FCMP++

To tackle privacy shortcomings with ring signatures, there is a consensus protocol update planned for Monero called FCMP++, which allows for an "anonymity set" of the entire chain. This protocol leverages a primitive for set membership called *Curve Trees*. Curve Trees allows one to efficiently prove that a "rerandomized" curve point exists in some set without revealing the element. In Monero, this set is defined as all "spendable" (i.e. unlocked and valid) transaction outputs on-chain. This randomization transformation is similar to "blinding" coin amounts in Pederson Commitments, and as a side effect, transaction output public keys *themselves* can be rerandomized on-chain. This fact opens the door for addressing protocols to add long-desired features, namely forward secrecy and outgoing view keys.

## 2. Features

### 2.1 Address generator

This tier is intended for merchant point-of-sale terminals. It can generate addresses on demand, but otherwise has no access to the wallet (i.e. it cannot recognize any payments in the blockchain).

### 2.2 Payment validator

This wallet tier combines the Address generator tier with the ability to also view received payments (including amounts). It is intended for validating paid orders. It cannot see outgoing payments and received change.

### 2.3 Full view-only wallets

Jamtis supports full view-only wallets that can identify spent outputs (unlike legacy view-only wallets), so they can display the correct wallet balance and list all incoming and outgoing transactions.

### 2.4 Janus attack mitigation

Janus attack is a targeted attack that aims to determine if two addresses A, B belong to the same wallet. Janus outputs are crafted in such a way that they appear to the recipient as being received to the wallet address B, while secretly using a key from address A. If the recipient confirms the receipt of the payment, the sender learns that they own both addresses A and B.

Jamtis prevents this attack by allowing the recipient to recognize a Janus output.

### 2.5 Conditional Forward Secrecy

As a result of leveraging the FCMP++ consensus protocol, Carrot has the ability to hide all transaction details (sender, receiver, amount) from observers with any possible level of computational power, as long as the observer does not know receiver's addresses. 

## 3. Notation

### 3.1 Miscellaneous definitions

1. The function `BytesToInt256(x)` deserializes a 256-bit little-endian integer from a 32-byte input.
1. The function `BytesToInt512(x)` deserializes a 512-bit little-endian integer from a 64-byte input.
1. The function `IntToBytes8(x)` serializes an integer into a little-endian encoded 8-byte output.
1. The function `IntToBytes4(x)` serializes an integer into a little-endian encoded 4-byte output.
1. The function `RandBytes(x)` generates a random x-byte string.
1. Concatenation is denoted by `||`.

### 3.2 Hash functions

The function <code>H<sub>b</sub>(x)</code> with parameters `b, x`, refers to the Blake2b hash function [[8](https://eprint.iacr.org/2013/322.pdf)] initialized as follows:

* The output length is set to `b` bytes.
* Hashing is done in sequential mode.
* The Personalization string is set to the ASCII value "Monero", padded with zero bytes.
* The input `x` is hashed.

The function `SecretDerive` is defined as:

<code>SecretDerive(x) = H<sub>32</sub>(x)</code>

The function `Keccak256(x)` refers to the SHA3-256 variant (AKA `r = 1088, c = 512, d = 256`) of the Keccak function [[citation](https://keccak.team/keccak.html)].

### 3.3 Elliptic curves

Two elliptic curves are used in this specification:

1. **Curve25519** - a Montgomery curve. Points on this curve include a cyclic subgroup <code>𝔾<sub>1</sub></code>.
1. **Ed25519** - a twisted Edwards curve. Points on this curve include a cyclic subgroup <code>𝔾<sub>2</sub></code>.

Both curves are birationally equivalent, so the subgroups <code>𝔾<sub>1</sub></code> and <code>𝔾<sub>2</sub></code> have the same prime order <code>ℓ = 2<sup>252</sup> + 27742317777372353535851937790883648493</code>. The total number of points on each curve is `8ℓ`.

#### 3.3.1 Curve25519

Curve25519 is used exclusively to serialize the Diffie-Hellman ephemeral pubkey [[9](https://cr.yp.to/ecdh/curve25519-20060209.pdf)] in transactions to match Jamtis behavior.

Public keys (elements of <code>𝔾<sub>1</sub></code>) are denoted by the capital letter `D` and are serialized as the x-coordinate of the corresponding Curve25519 point. Scalar multiplication is denoted by a space, e.g. <code>D = d B</code>.

#### 3.3.2 Ed25519

The Edwards curve is used for signatures and more complex cryptographic protocols [[10](https://ed25519.cr.yp.to/ed25519-20110926.pdf)]. The following generators are used:

|Point|Derivation|Serialized (hex)|
|-----|----------|----------|
| `G` | generator of <code>𝔾<sub>2</sub></code> | `5866666666666666666666666666666666666666666666666666666666666666`
| `H` | <code>H<sub>p</sub><sup>1</sup>(G)</code> | `8b655970153799af2aeadc9ff1add0ea6c7251d54154cfa92c173a0dd39c1f94`
| `T` | <code>H<sub>p</sub><sup>2</sup>("Monero generator T")</code> | `d1e6c1e625757d40bee4eed4fa6ad6447c426693f29dfb1c2fbb4c41e1f6bfd3`

Here <code>H<sub>p</sub><sup>1</sup></code> and <code>H<sub>p</sub><sup>2</sup></code> refer to two hash-to-point functions.

Private keys for Ed25519 are 32-byte integers denoted by a lowercase letter `k`. They are generated using one of the two following functions:

1. <code>KeyDerive2(x) = BytesToInt512(H<sub>64</sub>(x)) mod ℓ</code>
1. <code>KeyDerive2Legacy(x) = BytesToInt256(Keccak256(x)) mod ℓ</code>

Public keys (elements of <code>𝔾<sub>2</sub></code>) are denoted by the capital letter `K` and are serialized as 256-bit integers, with the lower 255 bits being the y-coordinate of the corresponding Ed25519 point and the most significant bit being the parity of the x-coordinate. Scalar multiplication is denoted by a space, e.g. <code>K = k G</code>.

#### 3.3.3 Public key conversion

We define two functions that can transform public keys between the two curves:

1. `ConvertPubkey1(D)` takes a Curve25519 public key `D` and outputs the corresponding Ed25519 public key `K` with an even-valued `x` coordinate.
2. `ConvertPubkey2(K)` takes an Ed25519 public key `K` and outputs the corresponding Curve25519 public key `D`.

The conversions between points on the curves are done with the equivalence `y = (u - 1) / (u + 1)`, where `y` is the ed25519 y-coordinate and `u` is the X25519 x-coordinate. Notice that the x-coordinates of ed25519 points and the y-coordinates of X25519 points are not considered.

Additionally, we define the function `NormalizeX(K)` that takes an Ed25519 point `K` and returns `K` if its `x` coordinate is even or `-K` if its `x` coordinate is odd.

## 4. Rerandomizable RingCT abstraction

Here we formally define an abstraction of the FCMP++ consensus layer called *Randomizable RingCT* which lays out the requirements that Carrot needs. All elliptic curve arithmetic occurs on ed25519.

### 4.1 Creating a transaction output

Transaction outputs are defined as the two points <code>(K<sub>o</sub>, C<sub>a</sub>)</code>. To create this transaction output, the sender must know `z, a` such that <code>C<sub>a</sub> = z G + a H</code> where <code>0 ≤ a < 2<sup>64</sup></code>. *Coinbase* transactions are slightly different in that `a` is stored publicly instead of <code>C<sub>a</sub></code>, and it is implied that <code>C<sub>a</sub> = G + a H</code>.

### 4.2 Spending a transaction output

To spend this output, the recipient must know `x, y, z, a` such that <code>K<sub>o</sub> = x G + y T</code> and <code>C<sub>a</sub> = z G + a H</code> where <code>0 ≤ a < 2<sup>64</sup></code>. Spending an output necessarily emits a *key image* (AKA "linking tag" or "nullifier") <code>L = x H<sub>p</sub><sup>2</sup>(K<sub>o</sub>)</code>. 

## 5. Wallets

### 5.1 Legacy key hierarchy

The following figure shows the overall hierarchy used for legacy wallet keys. Note that the master secret <code>s<sub>m</sub></code> doesn't exist for multisignature wallets. <code>k<sub>v</sub></code> will also be derived seperately from <code>k<sub>s</sub></code>.

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
|<code>k<sub>v</sub></code> | view key  | <code>k<sub>v</sub> = KeyDerive2Legacy(k<sub>s</sub>)</code>    | find and decode received e-notes, generate addresses |

### 5.2 New key hierarchy

The following figure shows the overall hierarchy one should use for new wallet keys. Users do not *have* to switch their key hierarchy in order to participate in the address protocol, but this heirarchy gives the best features and usability. Note that the master secret <code>s<sub>m</sub></code> doesn't exist for multisignature wallets.

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

There are 2 global wallet public keys for the new private key heirarchy. These keys are not usually published, but are needed by lower wallet tiers.

| Key | Name | Value |
|-----|------|-------|
|<code>K<sub>s</sub></code> | spend key    | <code>K<sub>s</sub> = k<sub>gi</sub> G + k<sub>ps</sub> T</code></code> |
|<code>K<sub>v</sub></code> | view key     | <code>K<sub>v</sub> = k<sub>v</sub> K<sub>s</sub></code>                |

Note: for legacy key heirarchies, <code>K<sub>s</sub> = k<sub>s</sub> G</code>.

### 5.4 New wallet access tiers

The new private key hierarchy enables the following useful wallet tiers:

| Tier         | Secret                      | Off-chain capabilities    | On-chain capabilities |
|--------------|-----------------------------|---------------------------|-----------------------|
| AddrGen      | <code>s<sub>ga</sub></code> | generate public addresses | none                  |
| ViewReceived | <code>k<sub>v</sub>         | all                       | view received         |
| ViewAll      | <code>s<sub>vb</sub></code> | all                       | view all              |
| Master       | <code>s<sub>m</sub></code>  | all                       | all                   |

#### 5.4.1 Address generator (AddrGen)

This wallet tier can generate public addresses for the wallet. It doesn't provide any blockchain access.

#### 5.4.2 Payment validator (ViewReceived)

This level provides the wallet with the ability to see all incoming payments, but cannot see any outgoing payments and change outputs. It can be used for payment processing or auditing purposes.

#### 5.4.3 View-only wallet (ViewAll)

This is a full view-only wallet than can see all incoming and outgoing payments (and thus can calculate the correct wallet balance).

#### 5.4.4 Master wallet (Master)

This tier has full control of the wallet.

## 6. Addresses

### 6.1 Address generation

There are two types of Cryptonote addresses: main addresses and subaddresses. There can only be a maximum of one main address per view key, but any number of subaddresses. However, by convention, subaddresses are generated from a "subaddress index", which is a tuple of two 32-bit unsigned integers <code>(j<sub>major</sub>, j<sub>minor</sub>)</code>, which allows for 2<sup>64</sup> addresses. The reason for the distinction between <code>j<sub>major</sub></code> and <code>j<sub>minor</sub></code> is simply for UX reasons. The "major" index is used to make separate "accounts" per wallet, which is used to compartamentalize input selection, change outputs, etc. The subaddress index `(0, 0)` is used to designate the main address, even though the key derivation is different. For brevity's sake, we use the label `j` as shorthand for <code>(j<sub>major</sub>, j<sub>minor</sub>)</code> and `0` as a shorthand for `(0, 0)`.

Each Cryptonote address derived from index `j` encodes the tuple <code>(K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>)</code>.

#### 6.1.1 Main address keys

The two public keys of the main address are constructed as:

* <code>K<sub>s</sub><sup>0</sup> = K<sub>s</sub></code>
* <code>K<sub>v</sub><sup>0</sup> = k<sub>v</sub> G</code>

#### 6.1.2 Subaddress keys (Legacy Heirarchy)

Under the legacy key heirarchy, the two public keys of a subaddress are constructed as:

* <code>K<sub>s</sub><sup>j</sup> = K<sub>s</sub> + k<sub>subext</sub><sup>j</sup> G</code>
* <code>K<sub>v</sub><sup>j</sup> = k<sub>v</sub> K<sub>s</sub><sup>j</sup></code>

Where subaddress extension key <code>k<sub>subext</sub><sup>j</sup> = KeyDerive2Legacy(IntToBytes8(8) \|\| k<sub>v</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code>. Notice that generating new subaddresses requires ViewReceived access to the wallet.

#### 6.1.3 Subaddress keys (New Heirarchy)

Under the new key heirarchy, the two public keys of a subaddress are constructed as:

* <code>K<sub>s</sub><sup>j</sup> = k<sub>a</sub><sup>j</sup> K<sub>s</sub></code>
* <code>K<sub>v</sub><sup>j</sup> = k<sub>a</sub><sup>j</sup> K<sub>v</sub></code>

Where address private key <code>k<sub>a</sub><sup>j</sup></code> are defined as follows:

| Symbol | Name | Definition |
|-------------------------- |-------------------------- |------------------------------|
|<code>k<sub>a</sub><sup>j</sup></code> | address private key  | <code>k<sub>a</sub><sup>j</sup> = KeyDerive2("jamtis_address_privkey" \|\| s<sub>gen</sub><sup>j</sup> \|\| K<sub>s</sub> \|\| K<sub>v</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code> |
| <code>s<sub>gen</sub><sup>j</sup></code> | address index generators | <code>s<sub>gen</sub><sup>j</sup> = SecretDerive("jamtis_address_index_generator" \|\| s<sub>ga</sub> \|\| IntToBytes4(j<sub>major</sub>) \|\| IntToBytes4(j<sub>minor</sub>))</code> |

The address index generator <code>s<sub>gen</sub><sup>j</sup></code> can be used to prove that the address was constructed from the index `j` and the public keys <code>K<sub>s</sub></code> and <code>K<sub>v</sub></code> without revealing <code>s<sub>ga</sub></code>.

#### 6.1.4 Integrated Addresses

Subaddresses are the recommended way to differentiate received enotes to your account for most users. However, there are some drawbacks to subaddresses. Most notably, in the past, generating subaddresses required ViewReceived access to the wallet (this is no longer the case with the new key heirarchy). This is not ideal for payment processors, so in practice a lot of processors turned to integrated addresses. Integrated addresses are simply main addresses with an 8-byte arbitrary string attched, called a *payment ID*. This payment ID is encrypted and then encoded into the transaction. In the reference wallet implementation, all transaction constructors who did not need to encode an encrypted payment ID into their transactions included a *dummy* payment ID by generating 8 random bytes. This makes the two types of sends indistinguishable on-chain from each other to external observers.

## 7. Transaction protocol

### 7.1 Transaction global fields

#### 7.1.1 Unlock time

The `unlock_time` field is removed [[15](https://github.com/monero-project/research-lab/issues/78)].

#### 7.1.2 Payment ID

A single 8-byte encrypted payment ID field is retained for 2-output non-coinbase transactions for backwards compability with legacy integrated addresses. When not sending to a legacy integrated address, `pid` is set to zero.

The payment ID `pid` is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>pid</sub></code>. The encryption mask is derived from the shared secrets of the payment e-note.

#### 7.1.3 View tag size specifier

A new 1-byte field `npbits` is added for future Jamtis transactions, but is unused in Carrot.

#### 7.1.4 Ephemeral public keys

Every 2-output transaction has one ephemeral public key <code>D<sub>e</sub></code>. Transactions with `N > 2` outputs have `N` ephemeral public keys (one for each output). Coinbase transactions always have one key per output.

### 7.2 E-note format

Each e-note represents an amount `a` sent to a Cryptonote address <code>(K<sub>s</sub><sup>j</sup>, K<sub>v</sub><sup>j</sup>)</code>.

An e-note contains the output public key <code>K<sub>o</sub></code>, the 3-byte combined view tag `vt`, the amount commitment <code>C<sub>a</sub></code>, encrypted *janus anchor* and encrypted amount <code>a<sub>enc</sub></code>. For coinbase transactions, the amount commitment <code>C<sub>a</sub></code> is omitted and the amount is not encrypted.

#### 7.2.1 The output key

The output key is constructed as <code>K<sub>o</sub> = K<sub>s</sub><sup>j</sup> + k<sub>g</sub><sup>o</sup> G + k<sub>t</sub><sup>o</sup> T</code>, where <code>k<sub>g</sub><sup>o</sup></code> and <code>k<sub>t</sub><sup>o</sup></code> are output key extensions.

#### 7.2.2 View tags

The view tag `vt` is the first 3 bytes of a hash of the ECDH exchange with the view key. This view tag is used to fail quickly in the scan process for enotes not intended for the current wallet. The bitsize of 24 was chosen as the fixed size because of Jamtis requirements.

#### 7.2.3 Amount commitment

The amount commitment is constructed as <code>C<sub>a</sub> = k<sub>a</sub> G + a H</code>, where <code>k<sub>a</sub></code> is the commitment mask and `a` is the amount. Coinbase transactions have implicitly <code>C<sub>a</sub> = a H + G</code>.

#### 7.2.4 Janus anchor

The Janus anchor `anchor` is a 16-byte encrypted string that provides protection against Janus attacks in Carrot. This space is to be used later for "address tags" in Jamtis. The anchor is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>anchor</sub></code>. In the case of normal transfers, <code>anchor=anchor<sup>nm</sup></code> is uniformly random, and used to rederive the enote ephemeral private key <code>k<sub>e</sub><sup>nm</sup></code> and check the enote ephemeral pubkey <code>D<sub>e</sub></code>. In *internal* or *self-send* transfers (where one sends money or change back to themselves) in 2-output transactions (i.e. with a shared <code>D<sub>e</sub></code>), <code>anchor=anchor<sup>sp</sup></code> is set to the first 16 bytes of a hash of the tx components as well as the generate-address secret <code>s<sub>ga</sub></code> (or <code>k<sub>v</sub></code> for legacy key heirarchies). Both of these derivation-and-check paths should only pass if either A) the sender constructed the enotes in a way which does not allow for a Janus attack or B) the sender knows the secret used to generate subaddresses and thus doesn't need to perform a Janus attack.

#### 7.2.5 Amount

The amount `a` is encrypted by exclusive or (XOR) with an encryption mask <code>m<sub>a</sub></code>.

### 7.3 E-note derivations

The e-note components are derived from the shared secret keys <code>K<sub>d</sub></code> and <code>K<sub>d</sub><sup>ctx</code>. The definitions of these keys are described below.

| Component | Name   | Derivation |
|-----------|--------|-----------|
|<code>vt</code>|view tag| <code>vt = SecretDerive("jamtis_secondary_view_tag" \|\| K<sub>d</sub> \|\| K<sub>o</sub>)</code> |
|<code>m<sub>anchor</sub></code>|encryption mask for `anchor`| <code>m<sub>anchor</sub> = SecretDerive("jamtis_encryption_mask_j'" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub>)</code> |
|<code>m<sub>a</sub></code>|encryption mask for `a`| <code>m<sub>a</sub> = SecretDerive("jamtis_encryption_mask_a" \|\| K<sub>d</sub><sup>ctx</sub> \|\| K<sub>o</sub>)</code> |
|<code>m<sub>pid</sub></code>|encryption mask for `pid`| <code>m<sub>pid</sub> = SecretDerive("jamtis_encryption_mask_pid" \|\| K<sub>d</sub><sup>ctx</sub> \|\| K<sub>o</sub>)</code> |
|<code>k<sub>a</sub></code>|amount commitment mask| <code>k<sub>a</sub> = KeyDerive2("jamtis_commitment_mask" \|\| K<sub>d</sub><sup>ctx</sup> \|\| enote_type)</code> |
|<code>k<sub>g</sub><sup>o</sup></code>|output key extension G| <code>k<sub>g</sub><sup>o</sup> = KeyDerive2("jamtis_key_extension_g" \|\| K<sub>d</sub><sup>ctx</sub> \|\| C<sub>a</sub>)</code> |
|<code>k<sub>t</sub><sup>o</sup></code>|output key extension T| <code>k<sub>t</sub><sup>o</sup> = KeyDerive2("jamtis_key_extension_t" \|\| K<sub>d</sub><sup>ctx</sub> \|\| C<sub>a</sub>)</code> |
|<code>anchor<sup>nm</sup></code>|janus anchor, normal| <code>anchor<sup>nm</sup> = RandBytes(16)</code> |
|<code>anchor<sup>sp</sup></code>|janus anchor, special| <code>anchor<sup>sp</sup> = SecretDerive("carrot_janus_anchor_special" \|\| K<sub>d</sub><sup>ctx</sup> \|\| K<sub>o</sub> \|\| s<sub>ga</sub> \|\| K<sub>s</sub>)</code> |
|<code>k<sub>e</sub></code>|ephemeral privkey| <code>k<sub>e</sub> = KeyDerive2("carrot_sending_key_normal" \|\| anchor<sup>nm</sup> \|\| a \|\| K<sub>s</sub><sup>j</sup> \|\| K<sub>v</sub><sup>j</sup> \|\| pid)</code> |

The variable `enote_type` is `"payment"` or `"change"` depending on the e-note type.

### 7.4 Ephemeral pubkey construction

The ephemeral pubkey <code>D</code>, a Curve25519 point, for a given enote is constructed differently based on what type of address one is sending to and how many outputs there are in the transaction. Here "special" means an *internal* enote in
a 2-out transaction. "Normal" refers to *external* enotes, or *internal* enotes in a >2-out transaction.

| Transfer Type            | <code>D<sub>e</sub></code> Derivation                                |
|--------------------------|----------------------------------------------------------------------|   
| Normal, to main address  | <code>ConvertPubkey2(k<sub>e</sub> G)</code>                         |
| Normal, to subaddress    | <code>ConvertPubkey2(k<sub>e</sub> K<sub>s</sub><sup>j</sup>)</code> |
| Special                  | <code>D<sub>e</sub><sup>other</sup></code>                           |

<code>D<sub>e</sub><sup>other</sup></code> refers to the ephemeral pubkey that would be derived on the *other* enote in a 2-out transaction. Reusing an ephemeral pubkey is only possible if we know a receiver's <code>k<sub>v</sub></code> (as we would for internal enotes), so we can "emulate" how the receiver would derive <code>K<sub>d</sub></code>. Using a shared <code>D<sub>e</sub></code> saves 32 bytes, and more importantly, a scalar multiplication per transaction.

### 7.5 Sender-receiver shared secrets

The shared secret keys <code>K<sub>d</sub></code> and <code>K<sub>d</sub><sup>ctx</sup></code> are used to encrypt/extend all components of Carrot transactions. Most components (except for the view tag for performance reasons) use <code>K<sub>d</sub><sup>ctx</sup></code> to encrypt components.

<code>K<sub>d</sub></code> can be derived the following ways:

|                       | Derivation                                                           |
|---------------------- | ---------------------------------------------------------------------|
|Sender, external       |    <code>NormalizeX(8 k<sub>e</sub> K<sub>v</sub><sup>j</sup>)</code>|
|Sender, internal       |<code>NormalizeX(8 k<sub>v</sub> ConvertPubkey1(D<sub>e</sub>))</code>|
|Recipient              |<code>NormalizeX(8 k<sub>v</sub> ConvertPubkey1(D<sub>e</sub>))</code>|

Then, <code>K<sub>d</sub><sup>ctx</sup></code> is derived as <code>K<sub>d</sub><sup>ctx</sup> = SecretDerive("jamtis_sender_receiver_secret" \|\| K<sub>d</sub> \|\| D<sub>e</sub> \|\| input_context)</code>.

Here `input_context` is defined as:

| transaction type | `input_context` |
|------------------|---------------------------------|
| coinbase         | block height                    |
| non-coinbase     | sorted list of spent key images |

The purpose of `input_context` is to make <code>K<sub>d</sub><sup>ctx</sup></code> unique for every transaction. This helps protect against the burning bug.

### 7.6 Janus outputs

In case of a Janus attack, the recipient will derive different values of the enote ephemeral pubkey <code>D<sub>e</sub></code> and Janus `anchor`, and thus will not recognize the output.

### 7.7 Internal enotes

Enotes which go to an address that belongs to the sending wallet are called "internal e-notes". The most common type are `"change"` e-notes, but internal "`payment"` enotes are also possible. For typical 2-output transactions, the change e-note can reuse the same value of <code>D<sub>e</sub></code> as the payment e-note.

#### 7.7.1 Mandatory change rule

Every transaction that spends funds from the wallet must produce at least one internal e-note, typically a change e-note. If there is no change left, an enote is added with a zero amount. This ensures that all transactions relevant to the wallet have at least one output. This allows for remote-assist "light weight" wallet servers to serve *only* the transactions relevant to the wallet, including any transaction that has spent key images. This rule also helps to optimize full wallet multi-threaded scanning by reducing state reuse.

#### 7.7.2 One payment, one change rule

In a 2-out transaction with two internal enotes, one enote's `enote_type` must be `"payment"`, and the other `"change"`.

In 2-out transactions, the ephemeral pubkey <code>D<sub>e</sub></code> is shared between enotes. `input_context` is also shared between the two enotes. Thus, if the two destination addresses share the same private view key <code>k<sub>v</sub></code> (i.e. they are two internal addresses) in a 2-out transaction, then <code>K<sub>d</sub><sup>ctx</sup></code> will be the same and the derivation paths will lead both enotes to have the same output pubkey, which is A) not allowed, B) bad for privacy, and C) would burn funds if allowed. However, note that the output pubkey extensions <code>k<sub>g</sub><sup>o</sup></code> and <code>k<sub>t</sub><sup>o</sup></code> bind to the amount commitment <code>C<sub>a</sub></code> which in turn binds to `enote_type`. Thus, if we want our two internal enotes to have unique derivations, then the `enote_type` needs to be unique.

### 7.8 Coinbase transactions

Coinbase transactions are not considered to be internal.

Miners should continue the practice of only allowing main addresses for the destinations of coinbase transactions in Carrot. This is because, unlike normal enotes, coinbase enotes do not contain an amount commitment, and thus scanning a coinbase enote commitment has no "hard target". If subaddresses can be the destinations of coinbase transactions, then the scanner *must* have their subaddress table loaded and populated to correctly scan coinbase enotes. If only main adddresses are allowed, then the scanner does not need the table and can instead simply check whether <code>K<sub>s</sub><sup>0</sup> ?= K<sub>o</sub> - k<sub>g</sub><sup>o</sup> G + k<sub>t</sub><sup>o</sup></code>.

### 7.9 Scanning performance

When scanning for received enotes, legacy wallets need to calculate <code>NormalizeX(8 k<sub>v</sub> ConvertPubKey1(D<sub>e</sub>))</code>. The operation <code>ConvertPubKey1(D<sub>e</sub>)</code> can be done during point decompression for free. The `NormalizeX()` function simply drops the x coordinate. The scanning performance for legacy wallets is therefore the same as in the old protocol.

Note: Legacy wallets use scalar multiplication in <code>𝔾<sub>2</sub></code> because the legacy view key <code>k<sub>v</sub></code> might be larger than 2<sup>252</sup>, which is not supported in the Montgomery ladder.

## 8. Desired security properties

### 8.1 Balance recovery security

The term "honest receiver" below means an entity with certain key material correctly executing the balance recovery side of the addressing protocol. In this section, all participants are assumed to adhere to the discrete log assumption.

#### 8.1.1 Spend Binding

If an honest receiver recovers `x` and `y` for an enote such that <code>K<sub>o</sub> = x G + y T</code>, then it is guaranteed within a security factor that no other entity without knowledge of <code>k<sub>ps</sub></code> (or <code>k<sub>s</sub></code> for legacy key heirarchies) will also be able to find `x` and `y`.

#### 8.1.2 Amount Commitment Binding

If an honest receiver recovers `z` and `a` for an enote such that <code>C = z G + a H</code>, then it is guaranteed within a security factor that no other entity without knowledge of <code>k<sub>v</sub></code> or <code>k<sub>e</sub></code> will also be able to find `z`.

#### 8.1.3 Burning-Bug Resistance

An honest receiver will only ever accept one enote containing a given <code>K<sub>o</sub></code>, rejecting all others.

#### 8.1.4 Janus Attack Resistance

A sender cannot construct an enote such that an honest receiver will accept it, and in doing do so, allow the sender to determine that two public addresses share the same <code>k<sub>v</sub></code>, whether it be a main address or subaddress.

### 8.2 Unlinkability

#### 8.2.1 Computational Address-Address Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if two non-integrated Cryptonote addresses share the same <code>k<sub>v</sub></code> with any better probability than random guessing.

#### 8.2.2 Computational Address-Enote Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if a Cryptonote addresses is the destination of an enote with any better probability than random guessing, even if they know the destination address.

#### 8.2.3 Computational Enote-Enote Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if two enotes have the same destination address with any better probability than random guessing, even if they know the destination address.

#### 8.2.4 Computational Enote-Key Image Unlinkability

A third party who cannot solve the Discrete Log Problem cannot determine if any key image is *the* key image for any enote with any better probability than random guessing, even if they know the destination address.

#### 8.2.5 Address-Conditional Forward Secrecy

A third party with unbounded compute power can learn no receiver or amount information about a transaction output, nor where it is spent, without knowing the receiver's public address.

## 9. Credits

Special thanks to everyone who commented and provided feedback on the original [Jamtis gist](https://gist.github.com/tevador/50160d160d24cfc6c52ae02eb3d17024). Some of the ideas were incorporated in this document.

## 10. References

*TODO*

## 11. Appendix A: Forward secrecy

Forward secrecy refers to the preservation of privacy properties of past transactions against a future adversary capable of solving the elliptic curve discrete logarithm problem (ECDLP), for example a quantum computer.

All e-notes sent to Cryptonote addresses under this protocol are forward-secret unless an address that belongs to the Cryptonote wallet is publicly known.

If an address is known to the ECDLP solver, all privacy is lost because the private view key <code>k<sub>v</sub></code> can be extracted from the address to recognize all incoming e-notes. Once incoming e-notes are identified, the ECDLP solver will be able to learn the associated key images by extracting <code>k<sub>g</sub><sup>a</sup> = DLog(K<sub>1</sub>, G)</code> and calculating <code>KI = (k<sub>g</sub><sup>a</sup> + k<sub>g</sub><sup>o</sup>) H<sub>p</sub>(K<sub>o</sub>)</code>.


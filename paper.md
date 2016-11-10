# Specializing decay for reference wrappers

ISO/IEC JTC1 SC22 WG21 Programming Language C++

D0498R0

Audience: Library Evolution

Date: 2016-11-8

_Jonathan Coe \<jbcoe@me.com\>_

_Walter E. Brown \<webrown.cpp@gmail.com\>_

## TL;DR

We propose to
specialize `std::decay` for `std::reference_wrapper` so that class template
argument deduction can handle reference wrappers
with no need for explicit deduction guides.

## Introduction

Before perfect forwarding, factory functions like `boost::make_shared` took a series of
`const` references as arguments:

```
template<typename T, typename T1, typename T2>
boost::shared_ptr<T> make_shared(const T1& t1, const T2& t2);
```

To pass a reference as an argument to such a function, one needed to use
`boost::reference_wrapper`, typically via its helper functions `boost::ref` and
`boost::cref`.
(`boost::reference_wrapper` is a copyable type that is implicitly
deducable to a reference.)

C++11's introduction of forwarding references
enabled ``perfect forwarding'',
thereby rendering unnecessary
the use of `reference_wrapper` when passing references into generic code.
`reference_wrapper` was nonetheless adopted in C++11,
as it is still needed to pass references into
factory functions that construct `pair`s and `tuple`s.

`std::make_pair` and `std::make_tuple` do not use perfect forwarding: that
would too readily result in a tuple of references, which is unlikely to be what
a user wanted. Instead these factories use `std::decay` to strip (cv- and
reference) qualifiers from the supplied types and construct a `pair` or `tuple`
of value types.

If a user wants a `tuple` of references then `make_tuple` must be explictly
passed a reference wrapper.

```
int x = 0;
double y = 0.0;

auto t1 = std::make_tuple(x, y);
  // t1 is std::tuple<int, double>;

auto t2 = std::make_tuple(std::ref(x), y);
  // t2 is std::tuple<int&, double>;
```

While this design works perfectly, it requires special casing of `make_tuple` and
`make_pair` to accommodate reference wrappers.


### Template argument deduction for class templates

C++17 introduces template argument deduction [over.match.class.deduct]
for class templates. A user can now write:

```
int x = 0;
double y = 0.0;

auto t = std::tuple(x, y);
  // t is std::tuple<int, double>;
```

and the compiler will deduce the type correctly.

Given this new language feature,
how should `reference_wrapper` interact with template
deduction for class templates?
A proposal [P00433R0] has suggested adding
deduction guides to specify the behaviour explicitly.

This seems unfortunate because the potential removal of `make_tuple` and similar
factory functions, with their domain-specific handling of reference wrappers, is
muddied by having to specify deduction guides explictly in order to recover the
(desirable) interaction with `reference wrapper`.

We instead propose modifications to `std::decay`
so that deduction guides  [temp.deduct.guide]
will give 'correct' behaviour for `reference_wrapper`:
unwrapping the wrapper.

### Specialization of `std::decay` for `std::reference_wrapper`

Here is an
expository implementation of `std::decay`
with the proposed special handling for reference wrappers:

```
template< class T >
struct decay {
private:
    typedef typename std::remove_reference<T>::type U;
public:
    typedef typename std::conditional<
        std::is_array<U>::value,
        typename std::remove_extent<U>::type*,
        typename std::conditional<
            std::is_function<U>::value,
            typename std::add_pointer<U>::type,
            typename std::remove_cv<U>::type
        >::type
    >::type type;
};

template< class T >
using decay_t = typename decay<T>::type;

// reference_wrapper value
template< class T >
struct decay<std::reference_wrapper<T>> {
	typedef T& type;
};

template< class T >
struct decay<const std::reference_wrapper<T>> {
	typedef T& type;
};

// reference_wrapper lvalue reference
template< class T >
struct decay<std::reference_wrapper<T>&> {
	typedef T& type;
};

template< class T >
struct decay<const std::reference_wrapper<T>&> {
	typedef T& type;
};

// reference_wrapper rvalue reference
template< class T >
struct decay<std::reference_wrapper<T>&&> {
	typedef T& type;
};

template< class T >
struct decay<const std::reference_wrapper<T>&&> {
	typedef T& type;
};
```

## Impact

Specializing `decay` for `reference_wrapper` makes writing factory functions easy:

```
template <typename ...Ts>
auto make_tuple(Ts&& ...ts) -> std::tuple<std::decay_t<Ts>...>
{
    return std::tuple<std::decay_t<Ts>...>(std::forward<Ts>(ts)...);
}
```

Further,
with the proposed change,
deduction guides can be specified using `std::decay` and users will not need
to write code to explicitly handle reference wrappers.

If a user does want a `tuple` of reference wrappers then it can still be explictly
specified:

```
int x = 0;
double y = 0.0;

auto t1 = std::tuple(ref(x), y);
  // t1 is std::tuple<int&, double>;

auto t2 = std::tuple<std::reference_wrapper<int>, double>(x, y);
  // t2 is std::tuple<std::reference_wrapper<int>, double>;
```

User-defined types can make full use of template deduction and reference
wrappers without any load on the user.  Although `reference_wrapper` is
often considered an
'expert-friendly' feature, this proposal's adoption would ensure
that user-defined class
templates will receive its benefits for free.

## Proposed wording

Amend Table 46's entry for the `decay` trait
as shown:

Comments:
Let `U` be `remove_reference_t<T>`
<font color="green"> and let `V` be `remove_cv_t<U>`</font>.
If `is_array_v<U>` is `true`,
the member typedef `type`
shall equal `remove_extent_t<U>*`.
If `is_function_v<U>` is true,
the member typedef `type`
shall equal `add_pointer_t<U>`.
<font color="green">If `V` is `reference_wrapper<X>`
for some type `X`,
the member typedef `type`
shall equal `V&`.</font>
Otherwise the member typedef type equals `remove_cv_t<U>`.
[Note: This behavior is similar
to the lvalue-to-rvalue (4.1),
array-to-pointer (4.2),
and function-to-pointer (4.3) conversions
applied when an lvalue expression is used as an rvalue,
but also strips cv-qualifiers
from class types
in order to more closely model
by-value argument passing.
—end note]


## Acknowledgements
The authors thank Howard Hinnant for useful discussion.

## References

[P00433R0] Mike Spertus & Walter E. Brown,
_"Toward a resolution of US7 and US14:
Integrating template deduction for class templates into the standard library"_,
2016-10-16.
